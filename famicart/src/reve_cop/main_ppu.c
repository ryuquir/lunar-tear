/* famicart rev F, U5 firmware: PPU-side coprocessor (Raspberry Pi Pico 2 sharing the PPU bus with U2).
 * core 1: answers PPU reads of the CHR slots it owns (profile coproc_chr_mask) from its drawing area.
 * core 0: takes the PPU command block ($5BF0-$5BFE) from U1's forwarded CPU writes and draws (cop_ppu.c);
 *         answers POLL with bit 7 = busy (U1 serves that as $5BFF). */
#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "hardware/pio.h"
#include "hardware/gpio.h"
#include "hardware/structs/sio.h"
#include "board.h"
#include "reve_linkhw.h"
#include "reve.pio.h"
#include "../core/profile.h"
#include "../core/reve/reve_link.h"
#include "../core/coproc/cop_ppu.h"
#include <string.h>
void reve_clock_init(void);

static uint8_t area[8192] __attribute__((aligned(4)));
static uint8_t *slot_ptr[8];                 /* owned slot -> its 1 KB in area, NULL = not ours */
static cop_ppu_t cop;
static volatile bool live; static uint16_t base = 0xFFFF;
static PIO pio_d = pio0; static uint sm_d;

static void __not_in_flash_func(ppu_core1)(void) {
    uint32_t last = 0xFFFFFFFFu;
    for (;;) {
        uint32_t a = sio_hw->gpio_in & 0x3FFFu;
        if (a == last) continue;
        last = a;
        uint32_t w = 0;
        if (live && a < 0x2000) { const uint8_t *p = slot_ptr[a >> 10]; if (p) w = 0xFF00u | p[a & 0x3FF]; }
        pio_sm_put(pio_d, sm_d, w);
    }
}

static void configure(const reve_load_t *ld) {
    const cart_profile_t *p = (const cart_profile_t *)ld->profile;
    memset(slot_ptr, 0, sizeof slot_ptr); base = 0xFFFF;
    if (!(ld->has_profile && profile_validate(p) && (p->coproc & COP_EN_PPU))) return;
    unsigned k = 0;
    for (unsigned n = 0; n < 8; n++) if (p->coproc_chr_mask & (1u << n)) slot_ptr[n] = area + (k++ << 10);
    memset(area, 0, sizeof area);
    cop_ppu_reset(&cop, area, k << 10);
    base = p->coproc_base ? p->coproc_base : COP_BASE_DEFAULT;
}

int main(void) {
    reve_clock_init();
    for (uint g = 0; g < 14; g++) { gpio_init(g); gpio_disable_pulls(g); gpio_set_input_hysteresis_enabled(g, true); }   /* no pad pull-downs on bus pins */
    gpio_init(PIN_PPU_RD); gpio_disable_pulls(PIN_PPU_RD); gpio_set_input_hysteresis_enabled(PIN_PPU_RD, true);
    gpio_init(PIN_LED); gpio_set_dir(PIN_LED, true);
    uint off = pio_add_program(pio_d, &reve_ppu_data_program);
    sm_d = pio_claim_unused_sm(pio_d, true);
    pio_sm_config dc = reve_ppu_data_program_get_default_config(off);
    sm_config_set_out_pins(&dc, PIN_PPU_D_BASE, 8); sm_config_set_jmp_pin(&dc, PIN_PPU_RD);
    sm_config_set_out_shift(&dc, true, false, 32);
    for (uint g = PIN_PPU_D_BASE; g < PIN_PPU_D_BASE + 8; g++) { pio_gpio_init(pio_d, g); gpio_disable_pulls(g); gpio_set_slew_rate(g, GPIO_SLEW_RATE_FAST); }
    pio_sm_set_consecutive_pindirs(pio_d, sm_d, PIN_PPU_D_BASE, 8, false);
    pio_sm_init(pio_d, sm_d, off, &dc);
    pio_sm_set_enabled(pio_d, sm_d, true);
    rlhw_init(pio1, PIN_LINK);
    multicore_launch_core1(ppu_core1);
    rl_dec_t dec; rl_dec_init(&dec); rl_event_t ev; reve_load_t ld;
    for (;;) {
        int s = rlhw_rx();
        if (s >= 0 && rl_dec_feed(&dec, (uint16_t)s, &ev)) {
            switch (ev.kind) {
            case RL_EV_LOAD: live = false; memcpy(&ld, dec.load, sizeof ld); configure(&ld); break;
            case RL_EV_COMMAND: if (ev.data == RL_C_LIVE) live = ev.arg && base != 0xFFFF; else if (ev.data == RL_C_RESET) live = false; break;
            case RL_EV_WRITE: { uint32_t o = (uint32_t)ev.addr - base; if (live && o >= COP_R_PPU_CMD && o < COP_R_PPU_STATUS) cop_ppu_write(&cop, (uint16_t)o, ev.data); break; }
            case RL_EV_POLL: if (ev.arg == RL_NODE_COP_PPU) rlhw_tx(cop.busy ? COP_ST_BUSY : 0); break;
            default: break;
            }
        }
        if (live && cop_ppu_run(&cop)) gpio_xor_mask(1u << PIN_LED);   /* draws straight into what core 1 serves */
    }
}
