/* famicart rev E, U2 firmware: Raspberry Pi Pico 2 wired straight to the PPU bus.
 *
 * PIO1   CIRAM /CE + A10 follow PPU A10-A13 through a 16-entry jump table (reve_ciram), rewritten whenever the
 *        mirroring / cartridge nametables change.
 * PIO0   PD0-7 are driven only while /RD is low (reve_ppu_data).
 * core 1 for every new PPU address: run the mapper's PPU hook (MMC2/4 latches, MMC5 scanline, 8x16 sets, split,
 *        ext. attributes), look the byte up and hand it to PIO0.
 * core 0 link: applies CPU writes (same mapper state as U1), CHR-RAM / nametable writes from U1's PPU address model,
 *        receives CHR at game load (into SRAM, or into this Pico's flash when it is larger than SRAM).
 */
#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "hardware/clocks.h"
#include "hardware/vreg.h"
#include "hardware/pio.h"
#include "hardware/gpio.h"
#include "hardware/flash.h"
#include "hardware/sync.h"
#include "hardware/structs/sio.h"
#include "board.h"
#include "reve_linkhw.h"
void reve_clock_init(void);
#include "reve.pio.h"
#include "../core/cartload.h"
#include "../core/mapper.h"
#include "../core/rom.h"
#include "../core/mappers/mmc5.h"
#include "../core/reve/reve_link.h"
#include "../core/reve/romcache.h"
#include <string.h>

_Static_assert(PIN_PPU_RD == 22 && PIN_CIRAM_CE == 26 && PIN_CIRAM_A10 == PIN_CIRAM_CE + 1, "pins assumed by the PIO setup");
#ifndef FC_CHR_POOL
#define FC_CHR_POOL (384 * 1024)
#endif

static cart_t cart; static rom_info_t info; static reve_load_t ld;
static volatile bool live, loaded;
static uint8_t chr_pool[FC_CHR_POOL] __attribute__((aligned(8)));
static uint8_t ciram[2][1024];                                /* shadow of the console's CIRAM (from U1's $2007 model) */
static romcache_t crc_cache; static uint16_t chr_page_slot[1024];
static bool chr_in_flash; static uint32_t chr_have_crc;       /* CRC of the CHR currently held (SRAM or flash) */
static uint8_t status = RL_ST_READY;
static PIO pio_d = pio0, pio_ce = pio1; static uint sm_d, sm_ce;

/* ---------------- CIRAM /CE table ---------------- */
static void ce_table(void) {
    for (unsigned i = 0; i < 16; i++) {
        unsigned ce = 1, a10 = (i & 1);
        if (i & 8) {                                          /* A13 = 1: nametable */
            unsigned nt = i & 3;
            if (!live) { ce = 0; a10 = i & 1; }               /* idle: vertical arrangement */
            else if (!(cart.nt_full || cart.nt_map[nt])) { ce = 0; a10 = cart.nt_ciram_a10[nt]; }
        }
        pio_ce->instr_mem[i] = (uint16_t)(pio_encode_jmp(reve_ciram_offset_top) | pio_encode_sideset_opt(2, (a10 << 1) | ce));
    }
}
static void tables_changed(void) {
    cart.tables_dirty = 0;
    if (chr_in_flash) { romcache_fix(&crc_cache, cart.chr_map, 8); romcache_fix(&crc_cache, cart.nt_map, 4); }
    ce_table();
}

/* ---------------- core 1: PPU bus ---------------- */
static void __not_in_flash_func(ppu_core1)(void) {
    cart_t *c = &cart;
    uint32_t last = 0xFFFFFFFFu; bool rd_prev = true, hooked = false;
    for (;;) {
        uint32_t in = sio_hw->gpio_in;
        uint32_t a = in & 0x3FFFu;
        bool rd = (in >> PIN_PPU_RD) & 1;
        if (!live) { if (a != last) { last = a; pio_sm_put(pio_d, sm_d, 0); } continue; }
        bool newread = !rd && rd_prev; rd_prev = rd;
        if (a != last || (newread && !hooked)) {
            last = a; hooked = !newread;
            const uint8_t *ov = NULL;
            if (c->has_ppu_hook) { c->ppu_override = NULL; c->mapper->ppu_addr(c, (uint16_t)a); ov = c->ppu_override; }
            uint32_t w;
            if (ov) w = 0xFF00u | *ov;
            else if (a < 0x2000) { const uint8_t *p = c->chr_map[a >> 10]; w = p ? (0xFF00u | p[a & 0x3FF]) : 0; }
            else {
                unsigned nt = (a >> 10) & 3; const uint8_t *p = c->nt_map[nt];
                if (p) w = 0xFF00u | p[a & 0x3FF];
                else if (c->nt_full) w = 0xFF00u | ciram[c->nt_ciram_a10[nt]][a & 0x3FF];
                else w = 0;                                   /* console CIRAM answers */
            }
            pio_sm_put(pio_d, sm_d, w);
        } else if (newread) hooked = false;
    }
}

/* ---------------- link events ---------------- */
static uint16_t vaddr; static uint8_t vinc;
static void vram_write(uint16_t a, uint8_t v) {
    a &= 0x3FFF;
    if (a < 0x2000) { if (cart.chr_wmask & (1u << (a >> 10))) cart.chr_map[a >> 10][a & 0x3FF] = v; return; }
    if (a >= 0x3F00) return;
    unsigned nt = (a >> 10) & 3;
    if (cart.nt_map[nt]) cart.nt_map[nt][a & 0x3FF] = v;
    else ciram[cart.nt_ciram_a10[nt]][a & 0x3FF] = v;
}
static void build_cart(void) {
    memset(&info, 0, sizeof info);
    info.source = ROM_SRC_DB; info.mapper = ld.mapper; info.submapper = ld.submapper; info.mirroring = ld.mirroring; info.battery = ld.battery; info.system = ld.system;
    info.prg_size = ld.prg_size; info.chr_size = ld.chr_size; info.chr_ram_size = ld.chr_ram_size; info.wram_size = ld.wram_size; info.sram_size = ld.sram_size;
    uint8_t *chr = NULL;
    if (ld.chr_size) chr = chr_in_flash ? (uint8_t *)(XIP_BASE + FC_FLASH_CHR) : chr_pool;
    loaded = cart_load_ext(&cart, NULL, chr, &info, ld.has_profile ? (const cart_profile_t *)ld.profile : NULL) == LOAD_OK;
    cart.bus_conflicts = false;                               /* U1 forwards the value after the bus conflict */
    if (loaded && chr_in_flash) {
        romcache_init(&crc_cache, chr, ld.chr_size, 10, chr_pool, sizeof chr_pool, chr_page_slot);
        romcache_preload(&crc_cache);
    }
    if (loaded) tables_changed();
    status = loaded ? RL_ST_READY : RL_ST_ERROR;
}
/* CHR larger than SRAM: staged 4 KB at a time into flash. Only allowed while not live (core 1 idle, no XIP use). */
static uint8_t stage[FLASH_SECTOR_SIZE] __attribute__((aligned(4))); static uint32_t stage_sector = 0xFFFFFFFFu;
static void stage_flush(void) {
    if (stage_sector == 0xFFFFFFFFu) return;
    uint32_t ints = save_and_disable_interrupts();
    flash_range_erase(FC_FLASH_CHR + stage_sector, FLASH_SECTOR_SIZE);
    flash_range_program(FC_FLASH_CHR + stage_sector, stage, FLASH_SECTOR_SIZE);
    restore_interrupts(ints);
    stage_sector = 0xFFFFFFFFu;
}
static void bulk_byte(uint32_t off, uint8_t v) {
    if (ld.chr_size <= sizeof chr_pool) { if (off < sizeof chr_pool) chr_pool[off] = v; return; }
    if (FC_FLASH_CHR + off >= FC_FLASH_END) return;
    uint32_t sec = off & ~(uint32_t)(FLASH_SECTOR_SIZE - 1);
    if (sec != stage_sector) { stage_flush(); memset(stage, 0xFF, sizeof stage); stage_sector = sec; }
    stage[off - sec] = v;
    if (off - sec == FLASH_SECTOR_SIZE - 1) { status = RL_ST_BUSY; stage_flush(); status = RL_ST_READY; }   /* U1 waits for READY every 4 KB */
}

int main(void) {
    reve_clock_init();
    for (uint g = 0; g < 14; g++) { gpio_init(g); gpio_set_input_hysteresis_enabled(g, true); }
    gpio_init(PIN_PPU_RD); gpio_set_input_hysteresis_enabled(PIN_PPU_RD, true);
    gpio_init(PIN_LED); gpio_set_dir(PIN_LED, true);
    /* PIO1: CIRAM /CE + A10 table at offset 0 */
    uint off_ce = pio_add_program(pio_ce, &reve_ciram_program);   /* .origin 0 */
    sm_ce = pio_claim_unused_sm(pio_ce, true);
    pio_sm_config cc = reve_ciram_program_get_default_config(off_ce);
    sm_config_set_in_pins(&cc, 10); sm_config_set_in_shift(&cc, false, false, 32);
    sm_config_set_sideset_pins(&cc, PIN_CIRAM_CE);
    pio_gpio_init(pio_ce, PIN_CIRAM_CE); pio_gpio_init(pio_ce, PIN_CIRAM_A10);
    gpio_set_slew_rate(PIN_CIRAM_CE, GPIO_SLEW_RATE_FAST); gpio_set_slew_rate(PIN_CIRAM_A10, GPIO_SLEW_RATE_FAST);
    pio_sm_set_pins_with_mask64(pio_ce, sm_ce, 1ull << PIN_CIRAM_CE, 3ull << PIN_CIRAM_CE);
    pio_sm_set_consecutive_pindirs(pio_ce, sm_ce, PIN_CIRAM_CE, 2, true);
    pio_sm_init(pio_ce, sm_ce, reve_ciram_offset_top, &cc);
    ce_table();
    pio_sm_set_enabled(pio_ce, sm_ce, true);
    /* PIO0: data */
    uint off_d = pio_add_program(pio_d, &reve_ppu_data_program);
    sm_d = pio_claim_unused_sm(pio_d, true);
    pio_sm_config dc = reve_ppu_data_program_get_default_config(off_d);
    sm_config_set_out_pins(&dc, PIN_PPU_D_BASE, 8); sm_config_set_jmp_pin(&dc, PIN_PPU_RD);
    sm_config_set_out_shift(&dc, true, false, 32);
    for (uint g = PIN_PPU_D_BASE; g < PIN_PPU_D_BASE + 8; g++) { pio_gpio_init(pio_d, g); gpio_set_slew_rate(g, GPIO_SLEW_RATE_FAST); gpio_set_drive_strength(g, GPIO_DRIVE_STRENGTH_8MA); }
    pio_sm_set_consecutive_pindirs(pio_d, sm_d, PIN_PPU_D_BASE, 8, false);
    pio_sm_init(pio_d, sm_d, off_d, &dc);
    pio_sm_set_enabled(pio_d, sm_d, true);
    rlhw_init(pio2, PIN_LINK);
    multicore_launch_core1(ppu_core1);

    rl_dec_t dec; rl_dec_init(&dec); rl_event_t ev; bool query = false;
    absolute_time_t blink = make_timeout_time_ms(300); bool led = false;
    for (;;) {
        int s = rlhw_rx();
        if (s >= 0 && rl_dec_feed(&dec, (uint16_t)s, &ev)) {
            switch (ev.kind) {
            case RL_EV_WRITE: if (loaded) { cart_cpu_write(&cart, ev.addr, ev.data); if (cart.tables_dirty) tables_changed(); } break;
            case RL_EV_READ:  if (loaded && cart.mapper->peek) cart.mapper->read(&cart, ev.addr, cart.open_bus); break;
            case RL_EV_PPU_ADDR: vaddr = ev.addr; vinc = ev.arg; break;
            case RL_EV_PPU_DATA: if (loaded) vram_write(vaddr, ev.data); vaddr = (uint16_t)((vaddr + (vinc ? 32 : 1)) & 0x3FFF); break;
            case RL_EV_POLL:
                if (ev.arg == RL_NODE_PPU) { uint8_t r = status; if (query) { r = (ld.chr_size && chr_have_crc == ld.chr_crc && status == RL_ST_READY) ? (RL_ST_READY | 0x02) : RL_ST_READY; query = false; } rlhw_tx(r); }
                break;
            case RL_EV_LOAD:
                live = false; memcpy(&ld, dec.load, sizeof ld); loaded = false; status = RL_ST_BUSY;
                chr_in_flash = ld.chr_size > sizeof chr_pool;
                if (!ld.chr_size) build_cart();
                else status = RL_ST_READY;                    /* waiting for CHR (or CHR_COMMIT when cached) */
                break;
            case RL_EV_BULK_ADDR: chr_have_crc = 0; break;
            case RL_EV_BULK_BYTE: bulk_byte(ev.off, ev.data); break;
            case RL_EV_COMMAND:
                if (ev.data == RL_C_RESET) { live = false; loaded = false; ce_table(); status = RL_ST_READY; }
                else if (ev.data == RL_C_LIVE) { live = ev.arg && loaded; memset(ciram, 0, sizeof ciram); ce_table(); }
                else if (ev.data == RL_C_CHR_QUERY) query = true;
                else if (ev.data == RL_C_CHR_COMMIT) { stage_flush(); chr_have_crc = ld.chr_crc; build_cart(); }
                else if (ev.data == RL_C_LED) gpio_put(PIN_LED, ev.arg & 1);
                break;
            default: break;
            }
        }
        if (live && cart.mapper_id == 5 && cart.s.mmc5.in_frame) {   /* MMC5 leaves the frame when the PPU stops reading */
            static uint32_t seen; static uint8_t last_idle;
            uint8_t idle = cart.s.mmc5.ppu_idle ^ cart.s.mmc5.match_count;
            uint32_t now = time_us_32();
            if (idle != last_idle) { last_idle = idle; seen = now; } else if (now - seen > 3) mmc5_frame_end(&cart);
        }
        if (chr_in_flash && live && romcache_service(&crc_cache, cart.chr_map, 8)) tables_changed();
        if (time_reached(blink)) { blink = make_timeout_time_ms(live ? 1000 : 250); gpio_put(PIN_LED, led = !led); }
    }
}
