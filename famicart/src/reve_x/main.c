/* famicart rev E, U3 firmware: Seeed XIAO RP2350, the "special chip".
 * Runs the same mapper state as U1 (every CPU write arrives over the link) and owns everything that needs exact
 * timing on the console's clocks:
 *   - /IRQ: CPU-cycle counters (VRC4/6/7, FME-7, N163, Bandai, Jaleco, Irem, RAMBO-1 ...) clocked by M2 itself,
 *     MMC3-style A12 counters clocked by the real PPU reads, MMC5 scanline IRQ from A13 + /RD.
 *   - MMC5 in-frame / IRQ-pending status for U1's $5204 (answered to U1's POLL).
 *   - expansion audio (VRC6, VRC7, MMC5, N163, Sunsoft 5B, ...) rendered to PWM.
 * core 1 owns the mapper state (M2 / PPU-read events and link writes are all applied there, in order);
 * core 0 decodes the link and renders audio. */
#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "hardware/clocks.h"
#include "hardware/vreg.h"
#include "hardware/pio.h"
#include "hardware/gpio.h"
#include "hardware/structs/sio.h"
#include "board.h"
#include "reve_linkhw.h"
void reve_clock_init(void);
#include "reve.pio.h"
#include "../core/cartload.h"
#include "../core/mapper.h"
#include "../core/mappers/mmc5.h"
#include "../core/audio/expaudio.h"
#include "../core/reve/reve_link.h"
#include <string.h>

_Static_assert(PIN_M2 == 5 && PIN_PPU_RD == 0 && PIN_PA13 == PIN_PA12 + 1, "pins assumed by reve.pio");
void audio_out_init(void); void audio_out_pump(void);

static cart_t cart; static reve_load_t ld;
static volatile bool live;
static volatile uint8_t status = RL_ST_READY;
static PIO pio_b = pio0; static uint sm_m2, sm_rd;

/* core0 -> core1: CPU writes / confirmed reads */
#define WQ 1024
static uint32_t wq[WQ]; static volatile uint32_t wq_w, wq_r;
#define WQ_READ 0x01000000u
static void wq_push(uint32_t e) { uint32_t n = (wq_w + 1) & (WQ - 1); while (n == wq_r) tight_loop_contents(); wq[wq_w] = e; __dmb(); wq_w = n; }

FC_INLINE void irq_out(bool on) { if (on) sio_hw->gpio_set = 1u << PIN_IRQ_GATE; else sio_hw->gpio_clr = 1u << PIN_IRQ_GATE; }

static void __not_in_flash_func(x_core1)(void) {
    cart_t *c = &cart;
    for (;;) {
        if (!live) { irq_out(false); while (!pio_sm_is_rx_fifo_empty(pio_b, sm_m2)) (void)pio_b->rxf[sm_m2]; while (!pio_sm_is_rx_fifo_empty(pio_b, sm_rd)) (void)pio_b->rxf[sm_rd]; wq_r = wq_w; continue; }
        bool mmc5 = c->mapper_id == 5;
        while (!pio_sm_is_rx_fifo_empty(pio_b, sm_m2)) {
            (void)pio_b->rxf[sm_m2];
            c->cpu_cycles++;
            if (c->has_cpu_cycle_hook) c->mapper->cpu_cycle(c);
        }
        while (!pio_sm_is_rx_fifo_empty(pio_b, sm_rd)) {
            uint32_t w = pio_b->rxf[sm_rd];
            bool a12 = (w >> 30) & 1, a13 = (w >> 31) & 1;
            if (mmc5) mmc5_a13_read(c, a13);
            else if (c->has_ppu_hook) c->mapper->ppu_addr(c, (uint16_t)((a13 ? 0x2000 : 0) | (a12 ? 0x1000 : 0)));
        }
        while (wq_r != wq_w) {
            uint32_t e = wq[wq_r]; wq_r = (wq_r + 1) & (WQ - 1);
            uint16_t a = (uint16_t)(e >> 8);
            if (e & WQ_READ) { if (c->mapper->peek) c->mapper->read(c, a, c->open_bus); }
            else cart_cpu_write(c, a, (uint8_t)e);
        }
        irq_out(c->irq_line);
        if (mmc5) status = (uint8_t)(RL_ST_VALID | RL_ST_READY | (c->s.mmc5.irq_pending ? RL_ST_MMC5_IRQ : 0) | (c->s.mmc5.in_frame ? RL_ST_MMC5_FRAME : 0));
    }
}

static void build_cart(void) {
    rom_info_t info; memset(&info, 0, sizeof info);
    info.source = ROM_SRC_DB; info.mapper = ld.mapper; info.submapper = ld.submapper; info.mirroring = ld.mirroring; info.battery = ld.battery; info.system = ld.system;
    info.prg_size = ld.prg_size; info.chr_size = ld.chr_size; info.chr_ram_size = ld.chr_ram_size; info.wram_size = ld.wram_size; info.sram_size = ld.sram_size;
    bool ok = cart_load_ext(&cart, NULL, NULL, &info, ld.has_profile ? (const cart_profile_t *)ld.profile : NULL) == LOAD_OK;
    cart.bus_conflicts = false;
    status = ok ? RL_ST_READY : RL_ST_ERROR;
}

static rl_dec_t dec;
/* link receive: interrupt-driven so audio rendering never lets the 8-symbol PIO FIFO overflow */
static void __not_in_flash_func(link_isr)(void) {
    int s; rl_event_t ev;
    while ((s = rlhw_rx()) >= 0) {
        if (!rl_dec_feed(&dec, (uint16_t)s, &ev)) continue;
        switch (ev.kind) {
        case RL_EV_WRITE: if (live) wq_push(((uint32_t)ev.addr << 8) | ev.data); break;
        case RL_EV_READ:  if (live) wq_push(WQ_READ | ((uint32_t)ev.addr << 8)); break;
        case RL_EV_POLL:  if (ev.arg == RL_NODE_X) rlhw_tx(status); break;
        case RL_EV_LOAD:  live = false; busy_wait_us(5); memcpy(&ld, dec.load, sizeof ld); build_cart(); break;
        case RL_EV_COMMAND:
            if (ev.data == RL_C_RESET) { live = false; expaudio_reset(&cart); status = RL_ST_READY; }
            else if (ev.data == RL_C_LIVE) { live = ev.arg && status != RL_ST_ERROR && cart.mapper; }
            else if (ev.data == RL_C_LED) gpio_put(PIN_LED, ev.arg & 1);
            break;
        default: break;
        }
    }
}

int main(void) {
    reve_clock_init();
    gpio_init(PIN_IRQ_GATE); gpio_set_dir(PIN_IRQ_GATE, true); gpio_put(PIN_IRQ_GATE, 0);
    gpio_init(PIN_LED); gpio_set_dir(PIN_LED, true);
    const uint ins[] = { PIN_M2, PIN_PA12, PIN_PA13, PIN_PPU_RD };
    for (unsigned i = 0; i < 4; i++) { gpio_init(ins[i]); gpio_disable_pulls(ins[i]); gpio_set_input_hysteresis_enabled(ins[i], true); }   /* no pad pull-downs on bus pins */
    uint off = pio_add_program(pio_b, &reve_m2_program);
    sm_m2 = pio_claim_unused_sm(pio_b, true);
    pio_sm_config c = reve_m2_program_get_default_config(off);
    sm_config_set_in_shift(&c, true, false, 32); sm_config_set_fifo_join(&c, PIO_FIFO_JOIN_RX);
    pio_sm_init(pio_b, sm_m2, off, &c); pio_sm_set_enabled(pio_b, sm_m2, true);
    uint off2 = pio_add_program(pio_b, &reve_rd_program);
    sm_rd = pio_claim_unused_sm(pio_b, true);
    pio_sm_config r = reve_rd_program_get_default_config(off2);
    sm_config_set_in_pins(&r, PIN_PA12); sm_config_set_in_shift(&r, true, false, 32); sm_config_set_fifo_join(&r, PIO_FIFO_JOIN_RX);
    pio_sm_init(pio_b, sm_rd, off2, &r); pio_sm_set_enabled(pio_b, sm_rd, true);
    rlhw_init(pio1, PIN_LINK);
    audio_out_init();
    multicore_launch_core1(x_core1);

    rl_dec_init(&dec);
    rlhw_rx_irq(link_isr);
    for (;;) audio_out_pump();
}
