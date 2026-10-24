/* famicart rev D, U2 firmware: CHR mapper. Mirrors U1's mapper state (every CPU register write arrives over the
 * link and is applied to a local cart_t), drives CHR flash/RAM bank lines from chr_map/nt_map, runs the PPU-side
 * mapper hooks on every PPU access and raises /IRQ_B. Also the CHR-flash programming agent (U1 supplies data
 * through the bridge). */
#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "hardware/clocks.h"
#include "hardware/gpio.h"
#include "hardware/sync.h"
#include "hardware/structs/sio.h"
#include "board.h"
#include "maplink.h"
#include "../core/cartload.h"
#include "../core/mapper.h"
#include "../core/rom.h"
#include "../core/mappers/../mapper_state.h"
#include <string.h>

static cart_t cart; static bool loaded; static uint32_t chr_base_bank;
static volatile bool live;                 /* false: boot state (CHR bank 0, H mirroring) */

/* ---- bank words: GPIO16-31 = CHR A10-A25 (gpio_out bits 16..31); GPIO32 SEL, 33 nFOURSCR, 34 CIRAM_A10 (gpio_hi_out bits 0..2) ---- */
static volatile uint32_t w_lo[16], w_hi[16];   /* index = PPU A10-A13 */
#define LO_MASK 0xFFFF0000u
#define HI_MASK 0x7u
#define HI_SEL  1u
#define HI_N4S  2u
#define HI_A10  4u

static void encode_all(cart_t *c) {
    uint32_t lo[16], hi[16];
    bool fourscr = false;
    for (int nt = 0; nt < 4; nt++) if (c->nt_map[nt]) fourscr = true;   /* any cart-supplied nametable => CIRAM off for all */
    for (int i = 0; i < 16; i++) {
        uint32_t bank = 0; bool sel_ram = false; uint32_t a10 = 0;
        if (i < 8) {
            uint8_t *p = c->chr_map[i];
            if ((uintptr_t)p >= FC_VROM_CHRRAM && (uintptr_t)p < FC_VROM_CHRRAM + FC_VROM_CHRRAM_SIZE) { sel_ram = true; bank = ((uintptr_t)p - FC_VROM_CHRRAM) >> 10; }
            else if ((uintptr_t)p >= FC_VROM_CHR && (uintptr_t)p < FC_VROM_CHR + 0x4000000u) bank = chr_base_bank + (((uintptr_t)p - FC_VROM_CHR) >> 10);
            a10 = c->nt_ciram_a10[0];
        } else {
            int nt = i & 3; uint8_t *p = c->nt_map[nt];
            if (p) { sel_ram = true; bank = ((uintptr_t)p - FC_VROM_CHRRAM) >> 10; }
            a10 = c->nt_ciram_a10[nt];
        }
        lo[i] = (bank & 0xFFFF) << 16;
        hi[i] = (sel_ram ? HI_SEL : 0) | (fourscr ? 0 : HI_N4S) | (a10 ? HI_A10 : 0);
    }
    uint32_t s = save_and_disable_interrupts();
    for (int i = 0; i < 16; i++) { w_lo[i] = lo[i]; w_hi[i] = hi[i]; }
    restore_interrupts(s);
    c->tables_dirty = 0;
}
static void encode_boot(void) {
    for (int i = 0; i < 16; i++) { w_lo[i] = 0; w_hi[i] = HI_N4S | (((i & 3) >= 2) ? HI_A10 : 0); }   /* CHR bank 0, horizontal mirroring */
}
FC_INLINE void irq_pin_set(bool assert_low) { if (assert_low) sio_hw->gpio_hi_clr = 1u << (PIN_IRQ - 32); else sio_hw->gpio_hi_set = 1u << (PIN_IRQ - 32); }

/* core 1: PPU bus watcher */
static void __not_in_flash_func(ppu_core1)(void) {
    uint32_t last = 0xFF, cur_lo = sio_hw->gpio_out & LO_MASK, cur_hi = sio_hw->gpio_hi_out & HI_MASK;
    bool rd_prev = true;
    for (;;) {
        uint32_t in = sio_hw->gpio_in;
        uint32_t idx = (in >> 10) & 15;
        if (idx != last) {
            last = idx;
            uint32_t lo = w_lo[idx], hi = w_hi[idx];
            if (lo != cur_lo) { sio_hw->gpio_togl = lo ^ cur_lo; cur_lo = lo; }
            if (hi != cur_hi) { sio_hw->gpio_hi_togl = hi ^ cur_hi; cur_hi = hi; }
        }
        bool rd = (in >> PIN_PPU_NRD) & 1;
        if (!rd && rd_prev && loaded && cart.has_ppu_hook) {
            cart.ppu_override = NULL; cart.mapper->ppu_addr(&cart, (uint16_t)(in & 0x3FFF));
            if (cart.tables_dirty) encode_all(&cart);
            irq_pin_set(cart.irq_line);
        }
        rd_prev = rd;
    }
}

/* ---- programming agent: U2 drives PA0-13, PnRD, PnWR, CHR_nWE, bank lines; U1 drives data via the bridge ---- */
static bool prog_mode; static uint32_t prog_addr; static bool prog_ram;
static void prog_set(bool on) {
    prog_mode = on;
    if (on) {
        multicore_reset_core1();
        for (uint g = 0; g < 14; g++) { gpio_set_dir(g, true); gpio_put(g, 0); }
        gpio_set_dir(PIN_PPU_NRD, true); gpio_put(PIN_PPU_NRD, 1); gpio_set_dir(PIN_PPU_NWR, true); gpio_put(PIN_PPU_NWR, 1);
        gpio_put(PIN_NBRIDGE, 0); gpio_put(PIN_BRIDGE_DIR, 1);
    } else {
        gpio_put(PIN_PPU_NRD, 1); gpio_put(PIN_PPU_NWR, 1); gpio_put(PIN_NBRIDGE, 1); gpio_put(PIN_BRIDGE_DIR, 1);
        for (uint g = 0; g < 16; g++) gpio_set_dir(g, false);
        multicore_launch_core1(ppu_core1);
    }
}
static inline void dly(unsigned n) { while (n--) __asm volatile("nop"); }
static void prog_apply_addr(void) {
    /* PA0-9 = addr & 0x3FF (PA10-13 stay 0 so A13=0 => cart region), bank lines = addr >> 10, SEL = ram */
    sio_hw->gpio_togl = (sio_hw->gpio_out ^ ((prog_addr & 0x3FF) | ((prog_addr >> 10) << 16))) & (0x3FFu | LO_MASK);
    sio_hw->gpio_hi_togl = (sio_hw->gpio_hi_out ^ (prog_ram ? HI_SEL : 0)) & HI_SEL;
}
static void prog_write_pulse(void) {
    prog_apply_addr(); gpio_put(PIN_BRIDGE_DIR, 1); dly(4);
    gpio_put(PIN_PPU_NWR, 0); dly(3);                /* PPU_ACC -> /CART_ACC -> chip /CE */
    gpio_put(PIN_CHR_NWE, 0); dly(8); gpio_put(PIN_CHR_NWE, 1); dly(2);
    gpio_put(PIN_PPU_NWR, 1);
}
static void prog_read_begin(void) { prog_apply_addr(); gpio_put(PIN_BRIDGE_DIR, 0); dly(2); gpio_put(PIN_PPU_NRD, 0); dly(20); }
static void prog_read_end(void) { gpio_put(PIN_PPU_NRD, 1); dly(2); gpio_put(PIN_BRIDGE_DIR, 1); }

/* ---- LOAD blob from U1 ---- */
static uint8_t blob[sizeof(rom_info_t) + sizeof(cart_profile_t) + 16]; static uint32_t blob_len, blob_fill;
static void apply_load(void) {
    struct { rom_info_t info; cart_profile_t prof; uint32_t chr_base_bank; uint8_t has_prof; uint8_t pad[3]; } b;
    if (blob_fill < sizeof b) { maplink_reply(LINK_R_ERROR); return; }
    memcpy(&b, blob, sizeof b);
    chr_base_bank = b.chr_base_bank;
    loaded = cart_load_from_info(&cart, NULL, &b.info, b.has_prof ? &b.prof : NULL) == LOAD_OK;
    if (loaded) encode_all(&cart);
    maplink_reply(loaded ? LINK_R_LOADED : LINK_R_ERROR);
}

int main(void) {
    set_sys_clock_khz(FC_SYS_CLOCK_KHZ, true);
    for (uint g = PIN_CHR_BANK_BASE; g < PIN_CHR_BANK_BASE + PIN_CHR_BANK_BITS; g++) { gpio_init(g); gpio_set_dir(g, true); gpio_put(g, 0); gpio_set_slew_rate(g, GPIO_SLEW_RATE_FAST); }
    for (uint g = 0; g < 16; g++) { gpio_init(g); gpio_set_dir(g, false); gpio_set_input_hysteresis_enabled(g, true); }
    const uint outs[] = { PIN_CHR_SEL, PIN_NFOURSCR, PIN_CIRAM_A10, PIN_LED, PIN_CHR_NWE, PIN_IRQ, PIN_NBRIDGE, PIN_BRIDGE_DIR };
    for (unsigned i = 0; i < sizeof outs / sizeof outs[0]; i++) { gpio_init(outs[i]); gpio_set_dir(outs[i], true); }
    gpio_put(PIN_CHR_SEL, 0); gpio_put(PIN_NFOURSCR, 1); gpio_put(PIN_CHR_NWE, 1); gpio_put(PIN_IRQ, 1); gpio_put(PIN_NBRIDGE, 1); gpio_put(PIN_BRIDGE_DIR, 1);
    gpio_init(PIN_CHR_RYBY); gpio_set_dir(PIN_CHR_RYBY, false); gpio_pull_up(PIN_CHR_RYBY);
    encode_boot();
    maplink_init();
    multicore_launch_core1(ppu_core1);
    uint32_t f; uint8_t led = 0; absolute_time_t blink = make_timeout_time_ms(500);
    for (;;) {
        if (maplink_poll(&f)) {
            unsigned t = (f >> 24) & 0xF; uint32_t p = f & 0xFFFFFF;
            switch (t) {
            case LINK_T_SYNC: break;
            case LINK_T_CPU_WRITE: if (loaded) { cart_cpu_write(&cart, (uint16_t)(p >> 8), (uint8_t)p); if (cart.tables_dirty && live) encode_all(&cart); irq_pin_set(cart.irq_line); } break;
            case LINK_T_CPU_READ:  if (loaded && cart.has_read_hook) { cart.mapper->read(&cart, (uint16_t)p, cart.open_bus); irq_pin_set(cart.irq_line); } break;
            case LINK_T_LOAD_BEGIN: blob_len = p; blob_fill = 0; break;
            case LINK_T_LOAD_DATA: for (int i = 0; i < 3 && blob_fill < blob_len && blob_fill < sizeof blob; i++) blob[blob_fill++] = (uint8_t)(p >> (8 * i)); break;
            case LINK_T_LOAD_END: apply_load(); break;
            case LINK_T_CMD: {
                unsigned sub = p >> 16, arg = p & 0xFFFF;
                if (sub == LINK_C_RESET) { loaded = false; live = false; encode_boot(); irq_pin_set(false); }
                else if (sub == LINK_C_ISOLATE) { prog_set(arg != 0); maplink_reply(LINK_R_ACK); }
                else if (sub == LINK_C_BOOT) { live = arg != 0; if (live && loaded) encode_all(&cart); else encode_boot(); }
                else if (sub == LINK_C_LED) gpio_put(PIN_LED, arg & 1);
                break; }
            case LINK_T_CHR_ADDR_HI: prog_addr = (prog_addr & 0xFFFFFF) | ((p & 3) << 24); prog_ram = (p & 4) != 0; break;
            case LINK_T_CHR_ADDR: prog_addr = (prog_addr & 0x3000000) | p; break;
            case LINK_T_CHR_WRITE: if (prog_mode) prog_write_pulse(); maplink_reply(LINK_R_ACK); break;
            case LINK_T_CHR_READ: if (prog_mode) prog_read_begin(); maplink_reply(LINK_R_ACK); break;
            case LINK_T_CHR_READ_END: if (prog_mode) prog_read_end(); maplink_reply(LINK_R_ACK); break;
            default: break;
            }
        }
        if (loaded && cart.mapper_id == 5) {              /* MMC5: tell U1 about in-frame / IRQ-pending so its $5204 reads are right */
            static uint8_t last_st = 0xFF;
            uint8_t st = (uint8_t)(0x80 | (cart.s.mmc5.in_frame ? 0x40 : 0) | (cart.s.mmc5.irq_pending ? 0x01 : 0));
            if (st != last_st) { last_st = st; maplink_reply(st); }
        }
        if (time_reached(blink)) { blink = make_timeout_time_ms(loaded ? 1000 : 200); gpio_put(PIN_LED, led ^= 1); }
    }
}
