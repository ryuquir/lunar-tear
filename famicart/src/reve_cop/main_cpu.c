/* famicart rev F, U4 firmware: CPU-side coprocessor (Raspberry Pi Pico 2 sharing the CPU bus with U1).
 * core 1: bus loop -- answers reads of its window $5800-$5BEF (relocatable) while /ROMSEL and /WS are high, takes
 *         window writes from the same PIO write capture as U1.
 * core 0: link (LOAD tells whether this cart enables the coprocessor and where the window is), runs commands. */
#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "hardware/clocks.h"
#include "hardware/pio.h"
#include "hardware/gpio.h"
#include "hardware/structs/sio.h"
#include "board.h"
#include "reve_linkhw.h"
#include "reve.pio.h"
#include "../core/profile.h"
#include "../core/reve/reve_link.h"
#include "../core/coproc/cop_cpu.h"
#include <string.h>
void reve_clock_init(void);
_Static_assert(PIN_WS == 27, "reve_wcap waits on GPIO27");

static cop_cpu_t cop;
static volatile bool enabled; static volatile uint16_t base = COP_BASE_DEFAULT;
static PIO pio_w = pio0; static uint sm_w;
#define DMASK (0xFFu << PIN_CPU_D_BASE)

static void __not_in_flash_func(bus_core1)(void) {
    uint32_t last = 0xFFFFFFFFu; uint8_t cur = 0, v = 0; bool oe = false, mine = false;
    for (;;) {
        uint32_t in = sio_hw->gpio_in, a = in & 0x7FFFu;
        bool romsel_low = !(in & (1u << PIN_ROMSEL)), ws_low = !(in & (1u << PIN_WS));
        if (a != last) {
            last = a;
            uint32_t off = a - base;
            mine = enabled && off < COP_R_PPU_CMD;
            if (mine) v = cop_cpu_read(&cop, (uint16_t)off);
        }
        bool drive = mine && !romsel_low && !ws_low;
        if (v != cur) { sio_hw->gpio_togl = (uint32_t)(v ^ cur) << PIN_CPU_D_BASE; cur = v; }
        if (drive != oe) { if (drive) sio_hw->gpio_oe_set = DMASK; else sio_hw->gpio_oe_clr = DMASK; oe = drive; }
        if (!pio_sm_is_rx_fifo_empty(pio_w, sm_w)) {
            uint32_t w = pio_w->rxf[sm_w];
            if (!((w >> PIN_ROMSEL) & 1)) continue;                     /* $8000-$FFFF: not ours */
            uint32_t off = (w & 0x7FFFu) - base;
            if (enabled && off < COP_R_PPU_CMD) { cop_cpu_write(&cop, (uint16_t)off, (uint8_t)(w >> PIN_CPU_D_BASE)); last = 0xFFFFFFFFu; }
        }
    }
}

int main(void) {
    reve_clock_init();
    for (uint g = 0; g < 15; g++) { gpio_init(g); gpio_disable_pulls(g); gpio_set_input_hysteresis_enabled(g, true); }   /* no pad pull-downs on bus pins */
    for (uint g = PIN_CPU_D_BASE; g < PIN_CPU_D_BASE + 8; g++) { gpio_init(g); gpio_disable_pulls(g); gpio_set_dir(g, false); gpio_put(g, 0); gpio_set_slew_rate(g, GPIO_SLEW_RATE_FAST); }
    gpio_init(PIN_ROMSEL); gpio_disable_pulls(PIN_ROMSEL); gpio_init(PIN_WS); gpio_disable_pulls(PIN_WS);
    gpio_init(PIN_LED); gpio_set_dir(PIN_LED, true);
    cop_cpu_reset(&cop);
    uint off = pio_add_program(pio_w, &reve_wcap_program);
    sm_w = pio_claim_unused_sm(pio_w, true);
    pio_sm_config cfg = reve_wcap_program_get_default_config(off);
    sm_config_set_in_pins(&cfg, 0); sm_config_set_in_shift(&cfg, false, false, 32);
    pio_sm_init(pio_w, sm_w, off, &cfg);
    uint32_t loops = (uint32_t)((uint64_t)FC_WCAP_DELAY_NS * (clock_get_hz(clk_sys) / 1000u) / 1000000u);
    pio_sm_put(pio_w, sm_w, loops > 4 ? loops - 4 : 1);
    pio_sm_set_enabled(pio_w, sm_w, true);
    rlhw_init(pio1, PIN_LINK);
    multicore_launch_core1(bus_core1);
    rl_dec_t dec; rl_dec_init(&dec); rl_event_t ev; reve_load_t ld;
    for (;;) {
        int s = rlhw_rx();
        if (s >= 0 && rl_dec_feed(&dec, (uint16_t)s, &ev)) {
            if (ev.kind == RL_EV_LOAD) {
                memcpy(&ld, dec.load, sizeof ld); enabled = false; cop_cpu_reset(&cop);
                const cart_profile_t *p = (const cart_profile_t *)ld.profile;
                if (ld.has_profile && profile_validate(p) && (p->coproc & COP_EN_CPU)) { base = p->coproc_base ? p->coproc_base : COP_BASE_DEFAULT; }
                else base = 0xFFFF;
            } else if (ev.kind == RL_EV_COMMAND && ev.data == RL_C_LIVE) enabled = ev.arg && base != 0xFFFF;
            else if (ev.kind == RL_EV_COMMAND && ev.data == RL_C_RESET) enabled = false;
            else if (ev.kind == RL_EV_POLL && ev.arg == RL_NODE_COP_CPU) rlhw_tx(enabled ? RL_ST_READY : RL_ST_BUSY);
        }
        if (cop_cpu_run(&cop)) gpio_xor_mask(1u << PIN_LED);
    }
}
