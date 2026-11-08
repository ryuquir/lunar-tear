/* famicart rev E, U1 firmware: Raspberry Pi Pico 2 wired straight to the CPU bus.
 *
 * core 1  bus loop (never returns, runs from SRAM): follows A0-A14 / /ROMSEL / /WS, drives D0-D7 with the PRG byte
 *         while /ROMSEL is low, with WRAM / mapper-register bytes for $4020-$7FFF, and with the boot handshake while no
 *         game is live; confirms reads with side effects (reve/rcommit.h); drains the PIO write capture.
 * core 0  applies CPU writes to the mapper, keeps the PPU address model for CHR-RAM, forwards everything to U2/U3 over
 *         the link, polls U3 for MMC5 status, fills the PRG page cache, USB commands (ROM library).
 */
#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "hardware/clocks.h"
#include "hardware/vreg.h"
#include "hardware/pio.h"
#include "hardware/gpio.h"
#include "hardware/structs/sio.h"
#include "hardware/structs/m33.h"
#include "board.h"
#include "reve_linkhw.h"
void reve_clock_init(void);
#include "reve_cpu.h"
#include "reve.pio.h"
#include "../core/cartload.h"
#include "../core/mapper.h"
#include "../core/rom.h"
#include "../core/reve/reve_link.h"
#include "../core/reve/ppu_track.h"
#include "../core/reve/rcommit.h"
#include "../core/reve/bootpark.h"
#include "../core/reve/romcache.h"
#include <stdio.h>
#include <string.h>

_Static_assert(PIN_WS == 27, "reve_wcap waits on GPIO27");

cart_t g_cart; rom_info_t g_info; bool g_running; lib_entry_t g_entry;
bootpark_t g_bp;
static romcache_t prc;
static uint16_t prg_page_slot[256];                        /* up to 2 MB PRG */
static uint8_t prg_pool[FC_PRG_POOL] __attribute__((aligned(8)));
static ppu_track_t trk;
static PIO pio_w = pio0; static uint sm_w;
volatile uint32_t st_reads, st_writes, st_evq_drop, st_link_drop, st_polls, st_poll_miss;

/* ---------------- core1 -> core0 event queue ---------------- */
#define EVQ 1024
static uint32_t evq[EVQ], evq_t[EVQ]; static volatile uint32_t evq_w, evq_r;
#define EV_READ 0x80000000u
FC_INLINE void evq_push(uint32_t e) { uint32_t n = (evq_w + 1) & (EVQ - 1); if (n == evq_r) { st_evq_drop++; return; } evq[evq_w] = e; evq_t[evq_w] = m33_hw->dwt_cyccnt; __dmb(); evq_w = n; }

/* ---------------- core 1: bus loop ---------------- */
#define DMASK (0xFFu << PIN_CPU_D_BASE)
static volatile bool serve_enable;                         /* false while the flash is being written */
static volatile bool rom_read_regs;                        /* mapper latches registers on ROM reads (234) */

/* $4020-$7FFF addresses at which a mapper read hook really drives the bus (otherwise: open bus, no drive). */
FC_INLINE bool low_window(const cart_t *c, uint16_t a) {
    switch (c->mapper_id) {
    case 5:  return a == 0x5204 || a == 0x5205 || a == 0x5206 || a == 0x5015 || (a >= 0x5C00 && c->s.mmc5.exram_mode >= 2);
    case 19: return a >= 0x4800 && a < 0x6000;
    case 36: return (a & 0xE100) == 0x4100;                            /* TXC 01-22000-400 readback */
    case 228: return a < 0x6000;                                       /* Action 52 4-bit RAM */
    default: return a >= 0x6000;
    }
}

static void __not_in_flash_func(bus_core1)(void) {
    cart_t *c = &g_cart; bootpark_t *bp = &g_bp;
    rcommit_t rc; rcommit_init(&rc);
    const uint32_t dwell = (uint32_t)((uint64_t)FC_DWELL_NS * (clock_get_hz(clk_sys) / 1000u) / 1000000u);
    m33_hw->demcr |= 1u << 24; m33_hw->dwt_ctrl |= 1u;      /* DWT cycle counter */
    uint32_t last = 0xFFFFFFFFu; uint8_t vrom = 0x4C, vlow = 0, cur_v = 0; bool rom_ok = true, low_ok = false, oe = false;
    for (;;) {
        uint32_t in = sio_hw->gpio_in;
        uint32_t a = in & 0x7FFFu;
        bool romsel_low = !(in & (1u << PIN_ROMSEL)), ws_low = !(in & (1u << PIN_WS));
        uint16_t ca;
        int rk = rcommit_sample(&rc, (uint16_t)a, romsel_low, ws_low, m33_hw->dwt_cyccnt, dwell, &ca);
        if (rk == RC_LOW && rcommit_wanted(ca, c->mapper && c->mapper->peek)) {
            if (bp->state != BP_RUN) bootpark_commit(bp, ca);
            evq_push(EV_READ | ((uint32_t)ca << 8));
        } else if (rk == RC_ROM && rom_read_regs && ca >= 0xFF80 && (ca < 0xFFA0 || (ca >= 0xFFE8 && ca < 0xFFF8))) {
            evq_push(EV_READ | ((uint32_t)ca << 8));                  /* Maxi 15 (234): registers latched by ROM reads */
        }
        if (a != last) {
            last = a;
            if (bp->state == BP_RUN && serve_enable) {
                const uint8_t *p = c->prg_map[4 + (a >> 13)];
                rom_ok = p != NULL; vrom = p ? p[a & 0x1FFF] : 0;
                low_ok = false;
                if (a >= 0x4020) {
                    const uint8_t *q = c->prg_map[a >> 13];
                    if (q && a >= 0x6000) { vlow = q[a & 0x1FFF]; low_ok = true; }
                    else if (c->has_read_hook && low_window(c, (uint16_t)a)) {
                        vlow = c->mapper->peek ? c->mapper->peek(c, (uint16_t)a, c->open_bus) : c->mapper->read(c, (uint16_t)a, c->open_bus);
                        low_ok = true;
                    }
                }
            } else {
                /* park / handshake: constants only, no flash access (the flash may be being written) */
                uint8_t g = 0;
                if (bp->state == BP_JUMP) { const uint8_t *p = c->prg_map[4 + (a >> 13)]; g = p ? p[a & 0x1FFF] : 0; }
                vrom = bootpark_rom(bp, (uint16_t)(a | 0x8000), g); rom_ok = true;
                low_ok = bootpark_low(bp, (uint16_t)a, &vlow);
            }
        }
        bool drive; uint8_t v;
        if (ws_low) { drive = false; v = cur_v; }
        else if (romsel_low) { drive = rom_ok; v = vrom; }
        else { drive = low_ok; v = vlow; }
        if (v != cur_v) { sio_hw->gpio_togl = (uint32_t)(v ^ cur_v) << PIN_CPU_D_BASE; cur_v = v; }
        if (drive != oe) { if (drive) sio_hw->gpio_oe_set = DMASK; else sio_hw->gpio_oe_clr = DMASK; oe = drive; }
        if (!pio_sm_is_rx_fifo_empty(pio_w, sm_w)) {
            uint32_t w = pio_w->rxf[sm_w];
            uint16_t wa = (uint16_t)((w & 0x7FFFu) | ((w >> PIN_ROMSEL) & 1u ? 0 : 0x8000u));
            uint8_t wd = (uint8_t)(w >> PIN_CPU_D_BASE);
            uint8_t *wm = c->prg_wmap[wa >> 13];
            if (wm && wa >= 0x6000 && wa < 0x8000 && !(c->mapper->flags & MF_WRITE_6000)) wm[wa & 0x1FFF] = wd;   /* WRAM: here and now */
            else if (wa >= 0x2000 && (wa < 0x4000 || wa >= 0x4020)) evq_push(((uint32_t)wa << 8) | wd);
            if (wa >= 0x6000 && wa < 0x8000) last = 0xFFFFFFFFu;                                              /* re-read the byte we serve */
        }
    }
}

static void bus_start(void) {
    for (uint g = 0; g < 15; g++) { gpio_init(g); gpio_set_input_hysteresis_enabled(g, true); }
    for (uint g = PIN_CPU_D_BASE; g < PIN_CPU_D_BASE + 8; g++) { gpio_init(g); gpio_set_dir(g, false); gpio_put(g, 0); gpio_set_slew_rate(g, GPIO_SLEW_RATE_FAST); gpio_set_drive_strength(g, GPIO_DRIVE_STRENGTH_8MA); }
    gpio_init(PIN_ROMSEL); gpio_init(PIN_WS);
    uint off = pio_add_program(pio_w, &reve_wcap_program);
    sm_w = pio_claim_unused_sm(pio_w, true);
    pio_sm_config cfg = reve_wcap_program_get_default_config(off);
    sm_config_set_in_pins(&cfg, 0);
    sm_config_set_in_shift(&cfg, false, false, 32);
    sm_config_set_fifo_join(&cfg, PIO_FIFO_JOIN_NONE);
    pio_sm_init(pio_w, sm_w, off, &cfg);
    uint32_t loops = (uint32_t)((uint64_t)FC_WCAP_DELAY_NS * (clock_get_hz(clk_sys) / 1000u) / 1000000u);
    pio_sm_put(pio_w, sm_w, loops > 4 ? loops - 4 : 1);
    pio_sm_set_enabled(pio_w, sm_w, true);
    multicore_launch_core1(bus_core1);
}

/* ---------------- link output (core 0) ---------------- */
#define SQ 4096
static uint16_t sq[SQ]; static unsigned sq_w, sq_r;
static void sq_put(const uint16_t *s, unsigned n) {
    for (unsigned i = 0; i < n; i++) { unsigned nx = (sq_w + 1) & (SQ - 1); if (nx == sq_r) { st_link_drop++; return; } sq[sq_w] = s[i]; sq_w = nx; }
}
static void sq_pump(void) { while (sq_r != sq_w && rlhw_tx_try(sq[sq_r])) sq_r = (sq_r + 1) & (SQ - 1); }
static void sq_flush(void) { while (sq_r != sq_w) sq_pump(); while (!rlhw_tx_idle()) tight_loop_contents(); }
void reve_link_cmd(uint8_t sub, uint8_t arg) { uint16_t s[3]; sq_put(s, rl_enc_cmd(s, sub, arg)); sq_flush(); }
/* POLL a node: returns its status byte or -1 */
int reve_link_poll(uint8_t node, uint32_t timeout_us) {
    uint16_t s[2]; sq_flush(); rlhw_rx_reset();                 /* TX idle: whatever is in the RX FIFO is our own echo */
    unsigned n = rl_enc_poll(s, node); for (unsigned i = 0; i < n; i++) rlhw_tx(s[i]);
    int r;
    do { r = rlhw_rx_wait(timeout_us); } while (r >= 0 && (r & RL_START));   /* a stray frame start is not an answer */
    st_polls++; if (r < 0) st_poll_miss++;
    return r < 0 ? -1 : (r & 0xFF);
}

/* ---------------- core 0: event handling ---------------- */
static uint16_t last_fwd_addr = 0xFFFF; static uint16_t remote_vaddr = 0xFFFF; static uint8_t remote_inc = 0xFF;
static bool fwd_ppu; static uint32_t mmc5_ack_until;
static bool cycles_from_time; static uint32_t rmw_gap, last_wt;   /* synthetic cpu_cycles for MMC1's RMW rule */
static void forward_write(uint16_t a, uint8_t v) {
    uint16_t s[3]; unsigned n = (a == (uint16_t)(last_fwd_addr + 1)) ? rl_enc_seq(s, v) : rl_enc_write(s, a, v);
    sq_put(s, n); last_fwd_addr = a;
}
static void fix_tables(void) {
    if (!g_cart.tables_dirty) return;
    g_cart.tables_dirty = 0;
    romcache_fix(&prc, (uint8_t **)&g_cart.prg_map[3], 5);
}
static void handle_event(uint32_t e) {
    cart_t *c = &g_cart;
    uint16_t a = (uint16_t)(e >> 8); uint8_t v = (uint8_t)e;
    if (e & EV_READ) {
        st_reads++;
        if ((a & 0xE000) == 0x2000) { ppu_track_read(&trk, a); return; }
        if (a >= 0x4C4C && a <= 0x4C4E && g_bp.state != BP_RUN) return;
        if (g_running && c->mapper->peek && a >= 0x4020) {
            c->mapper->read(c, a, c->open_bus);
            fix_tables();
            uint16_t s[3]; sq_put(s, rl_enc_read(s, a));
            if (c->mapper_id == 5 && a == 0x5204) mmc5_ack_until = time_us_32() + 40;
        }
        return;
    }
    st_writes++;
    if (!g_running) return;
    if (a < 0x4000) {
        uint16_t va;
        if (ppu_track_write(&trk, a, v, &va) && fwd_ppu && va < 0x3F00) {
            uint16_t s[3];
            if (va != remote_vaddr || trk.inc32 != remote_inc) { sq_put(s, rl_enc_ppu_addr(s, va, trk.inc32)); remote_inc = trk.inc32; }
            sq_put(s, rl_enc_ppu_data(s, v)); remote_vaddr = (uint16_t)((va + (trk.inc32 ? 32 : 1)) & 0x3FFF);
        }
        if ((c->mapper->flags & MF_SNOOP_PPU_REGS) && (a & 0xE007) <= 0x2001) { cart_cpu_write(c, (uint16_t)(0x2000 | (a & 1)), v); forward_write((uint16_t)(0x2000 | (a & 1)), v); }
        return;
    }
    if ((c->mapper->flags & MF_BUS_CONFLICT) && c->bus_conflicts && a >= 0x8000) { const uint8_t *p = c->prg_map[a >> 13]; if (p) v &= p[a & 0x1FFF]; }
    cart_cpu_write(c, a, v);
    forward_write(a, v);
    fix_tables();
}

/* MMC5 status ($5204) lives on U3, which sees the PPU: poll it every few microseconds while idle. */
static void mmc5_poll(void) {
    static uint32_t next;
    uint32_t now = time_us_32();
    if ((int32_t)(now - next) < 0 || sq_r != sq_w) return;
    next = now + 4;
    int st = reve_link_poll(RL_NODE_X, 4);
    if (st < 0 || !(st & RL_ST_VALID)) return;
    g_cart.s.mmc5.in_frame = (st & RL_ST_MMC5_FRAME) ? 1 : 0;
    if ((int32_t)(time_us_32() - mmc5_ack_until) > 0) g_cart.s.mmc5.irq_pending = (st & RL_ST_MMC5_IRQ) ? 1 : 0;
}

/* U1 does not see M2: cycle-counter registers that games read back (N163 $5000/$5800) are advanced from the clock. */
static void cycle_catchup(void) {
    static uint32_t last_us; static uint32_t frac;
    cart_t *c = &g_cart;
    uint32_t now = time_us_32(), d = now - last_us; last_us = now;
    if (!g_running || !c->has_cpu_cycle_hook || !c->mapper->peek || c->mapper_id == 5) return;
    if (d > 2000) d = 2000;
    frac += d * 1790u; uint32_t n = frac / 1000u; frac %= 1000u;
    while (n--) { c->cpu_cycles++; c->mapper->cpu_cycle(c); }
}

/* ---------------- game load ---------------- */
const lib_header_t *lib_hdr_flash(void) { return (const lib_header_t *)(XIP_BASE + FC_FLASH_LIB); }
const lib_entry_t *lib_entry_flash(unsigned i) { return (const lib_entry_t *)(XIP_BASE + FC_FLASH_LIB + LIB_ENTRY_SIZE * (1 + i)); }

void reve_park(void) {
    bootpark_park(&g_bp); g_running = false;
    reve_link_cmd(RL_C_LIVE, 0);
}
static bool wait_ready(uint8_t node, uint32_t ms) {
    absolute_time_t t = make_timeout_time_ms(ms);
    while (!time_reached(t)) { int s = reve_link_poll(node, 50); if (s >= 0 && (s & 0x1F) == RL_ST_READY) return true; if (s == RL_ST_ERROR) return false; sleep_us(200); }
    return false;
}
bool reve_boot(unsigned slot) {
    const lib_entry_t *e = lib_entry_flash(slot);
    if (e->magic != LIB_MAGIC) return false;
    g_entry = *e;
    const uint8_t *prg = (const uint8_t *)(XIP_BASE + FC_FLASH_DATA + e->prg_off), *chr = prg + e->prg_size;
    if (!rom_inspect_header(e->header, e->prg_size + e->chr_size, e->data_crc, &g_info)) return false;
    reve_park();
    const cart_profile_t *prof = (e->flags & 1) ? &e->profile : NULL;
    if (cart_load_ext(&g_cart, prg, NULL, &g_info, prof) != LOAD_OK) return false;
    romcache_init(&prc, prg, g_info.prg_size, 13, prg_pool, sizeof prg_pool, prg_page_slot);
    romcache_preload(&prc);
    g_cart.tables_dirty = 1; fix_tables();
    /* describe the cart to U2/U3 */
    reve_load_t ld; memset(&ld, 0, sizeof ld);
    ld.mapper = g_info.mapper; ld.submapper = g_info.submapper; ld.mirroring = g_info.mirroring; ld.battery = g_info.battery; ld.system = g_info.system;
    ld.prg_size = g_info.prg_size; ld.chr_size = g_info.chr_size; ld.chr_ram_size = g_info.chr_ram_size; ld.wram_size = g_info.wram_size; ld.sram_size = g_info.sram_size;
    ld.chr_crc = e->chr_size ? fc_crc32(0, chr, e->chr_size) : 0;
    if (prof) { ld.has_profile = 1; memcpy(ld.profile, prof, sizeof *prof < sizeof ld.profile ? sizeof *prof : sizeof ld.profile); }
    rom_read_regs = g_cart.mapper_id == 234;
    fwd_ppu = true;                                               /* always: CHR-RAM, cart nametables and U2's CIRAM shadow (some boards switch to RAM later) */
    ld.flags = (g_cart.chr_is_ram ? 1 : 0) | (fwd_ppu ? 2 : 0);
    reve_link_cmd(RL_C_RESET, 0);
    uint16_t s[RL_LOAD_MAX + 4]; unsigned n = rl_enc_load_head(s, sizeof ld);
    for (unsigned i = 0; i < sizeof ld; i++) s[n++] = ((const uint8_t *)&ld)[i];
    sq_put(s, n); sq_flush();
    /* CHR to U2 unless it already holds this CHR */
    if (e->chr_size) {
        reve_link_cmd(RL_C_CHR_QUERY, 0);
        int have = reve_link_poll(RL_NODE_PPU, 2000);
        if (have != (RL_ST_READY | 0x02)) {
            sq_put(s, rl_enc_bulk_addr(s, 0)); sq_flush();
            for (uint32_t off = 0; off < e->chr_size; off += 256) {
                unsigned k = e->chr_size - off < 256 ? e->chr_size - off : 256;
                sq_put(s, rl_enc_bulk(s, chr + off, k)); sq_flush();
                if ((off & 0xFFF) == 0xF00 && !wait_ready(RL_NODE_PPU, 1000)) { printf("ERR: U2 stopped answering during the CHR transfer\n"); return false; }   /* U2 may be writing a flash sector */
            }
        }
        reve_link_cmd(RL_C_CHR_COMMIT, 0);
    }
    bool ok2 = wait_ready(RL_NODE_PPU, 20000), ok3 = wait_ready(RL_NODE_X, 500);
    if (!ok2) printf("WARN: U2 (PPU) did not report ready\n");
    if (!ok3) printf("WARN: U3 (XIAO) did not report ready\n");
    ppu_track_reset(&trk); remote_vaddr = 0xFFFF; remote_inc = 0xFF; last_fwd_addr = 0xFFFF;
    rmw_gap = clock_get_hz(clk_sys) / 1000000u * 840u / 1000u; last_wt = 0;
    cycles_from_time = !(g_cart.has_cpu_cycle_hook && g_cart.mapper->peek);   /* else cycle_catchup() owns cpu_cycles */
    evq_r = evq_w;
    reve_link_cmd(RL_C_LIVE, 1);
    g_running = true;
    bootpark_arm(&g_bp);                                          /* the CPU leaves JMP $4C4C through JMP ($FFFC) */
    return true;
}

/* flash writes: stop serving from flash first (park), then resume */
void reve_flash_begin(void) { reve_park(); serve_enable = false; sleep_ms(2); }
void reve_flash_end(void) { serve_enable = true; }

int main(void) {
    reve_clock_init();
    bootpark_init(&g_bp); serve_enable = true;
    bus_start();                                                   /* park the CPU as early as possible */
    rlhw_init(pio1, PIN_LINK);
    stdio_init_all();
    usb_cmd_init();
    sleep_ms(300);                                                 /* let U2/U3 boot */
    const lib_header_t *h = lib_hdr_flash();
    if (h->magic == LIB_MAGIC && !reve_boot(h->current)) printf("boot of slot %lu failed\n", (unsigned long)h->current);
    absolute_time_t info_t = make_timeout_time_ms(3000);
    for (;;) {
        unsigned budget = 64;
        while (evq_r != evq_w && budget--) {
            uint32_t e = evq[evq_r], t = evq_t[evq_r]; evq_r = (evq_r + 1) & (EVQ - 1);
            /* U1 has no M2: give cycle-sensitive mappers (MMC1's "ignore the second write of a RMW") the CPU cycle of
             * the write, derived from the core-1 timestamp. */
            if (cycles_from_time && !(e & EV_READ)) {
                /* writes on back-to-back CPU cycles are ~559 ns apart, the next possible gap is ~1118 ns */
                g_cart.cpu_cycles += ((uint32_t)(t - last_wt) < rmw_gap) ? 1u : 3u; last_wt = t;
            }
            handle_event(e);
        }
        sq_pump();
        if (g_running && g_cart.mapper_id == 5) mmc5_poll();
        if (romcache_service(&prc, (uint8_t *const *)&g_cart.prg_map[3], 5)) { g_cart.tables_dirty = 1; fix_tables(); }
        cycle_catchup();
        if (evq_r == evq_w) usb_cmd_poll();
        if (time_reached(info_t)) { info_t = make_timeout_time_ms(10000); usb_cmd_print_info(); }
    }
}
