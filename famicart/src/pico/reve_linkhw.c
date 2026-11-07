#include "reve_linkhw.h"
#include "pico/stdlib.h"
#include "hardware/clocks.h"
#include "hardware/irq.h"
#include "reve.pio.h"

static PIO lp; static uint sm_tx, sm_rx, tx_off; static unsigned lpin;
static volatile uint32_t echo; static uint32_t last_tx_us;

void rlhw_init(PIO pio, unsigned pin) {
    lp = pio; lpin = pin;
    float div = (float)clock_get_hz(clk_sys) / (8.0f * RL_BAUD);
    pio_gpio_init(lp, pin); gpio_pull_up(pin); gpio_set_slew_rate(pin, GPIO_SLEW_RATE_FAST); gpio_set_drive_strength(pin, GPIO_DRIVE_STRENGTH_8MA);
    uint off = pio_add_program(lp, &reve_link_tx_program); tx_off = off;
    sm_tx = pio_claim_unused_sm(lp, true);
    pio_sm_config c = reve_link_tx_program_get_default_config(off);
    sm_config_set_out_pins(&c, pin, 1); sm_config_set_set_pins(&c, pin, 1); sm_config_set_sideset_pins(&c, pin);
    sm_config_set_out_shift(&c, true, false, 32);
    sm_config_set_fifo_join(&c, PIO_FIFO_JOIN_TX);
    sm_config_set_clkdiv(&c, div);
    pio_sm_set_pins_with_mask64(lp, sm_tx, 1ull << pin, 1ull << pin);
    pio_sm_set_consecutive_pindirs(lp, sm_tx, pin, 1, false);
    pio_sm_init(lp, sm_tx, off, &c);
    pio_sm_set_enabled(lp, sm_tx, true);
    uint off2 = pio_add_program(lp, &reve_link_rx_program);
    sm_rx = pio_claim_unused_sm(lp, true);
    pio_sm_config r = reve_link_rx_program_get_default_config(off2);
    sm_config_set_in_pins(&r, pin); sm_config_set_jmp_pin(&r, pin);
    sm_config_set_in_shift(&r, true, false, 32);
    sm_config_set_fifo_join(&r, PIO_FIFO_JOIN_RX);
    sm_config_set_clkdiv(&r, div);
    pio_sm_init(lp, sm_rx, off2, &r);
    pio_sm_set_enabled(lp, sm_rx, true);
}
bool rlhw_tx_try(uint16_t sym) {
    if (pio_sm_is_tx_fifo_full(lp, sm_tx)) return false;
    pio_sm_put(lp, sm_tx, sym & 0x3FF); echo++; last_tx_us = time_us_32(); return true;
}
void rlhw_tx(uint16_t sym) { while (!rlhw_tx_try(sym)) tight_loop_contents(); }
bool rlhw_tx_idle(void) {
    if (!pio_sm_is_tx_fifo_empty(lp, sm_tx)) return false;
    return pio_sm_get_pc(lp, sm_tx) == tx_off;                     /* back on "pull block": the stop bit is out */
}
int rlhw_rx(void) {
    for (;;) {
        if (pio_sm_is_rx_fifo_empty(lp, sm_rx)) {
            if (echo && (time_us_32() - last_tx_us) > 30) echo = 0;     /* lost echo: re-sync */
            return -1;
        }
        int s = (int)(pio_sm_get(lp, sm_rx) >> 22);
        if (echo) { echo--; continue; }
        return s;
    }
}
int rlhw_rx_wait(uint32_t timeout_us) {
    uint32_t t0 = time_us_32();
    for (;;) { int s = rlhw_rx(); if (s >= 0) return s; if (time_us_32() - t0 > timeout_us) return -1; }
}
void rlhw_rx_irq(void (*handler)(void)) {
    uint irqn = (lp == pio0) ? PIO0_IRQ_0 : (lp == pio1) ? PIO1_IRQ_0 : PIO2_IRQ_0;
    pio_set_irq0_source_enabled(lp, (enum pio_interrupt_source)(pis_sm0_rx_fifo_not_empty + sm_rx), true);
    irq_set_exclusive_handler(irqn, handler); irq_set_priority(irqn, 0); irq_set_enabled(irqn, true);
}
void rlhw_rx_reset(void) {
    while (!pio_sm_is_rx_fifo_empty(lp, sm_rx)) (void)pio_sm_get(lp, sm_rx);
    pio_sm_clear_fifos(lp, sm_rx); echo = 0;
}
