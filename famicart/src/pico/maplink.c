#include "maplink.h"
#include "board.h"
#include "pico/stdlib.h"
#include "hardware/pio.h"
#include "hardware/clocks.h"
#include "maplink.pio.h"

#define LINK_BIT_HZ   25000000u   /* 2 PIO cycles per bit -> 32 bits in 1.3 us */
#define RET_BAUD      2000000u

static PIO lpio = pio1;
static uint sm_link, sm_ret;

#if FC_ROLE_PRG
void maplink_init(void) {
    pio_set_gpio_base(lpio, 16);
    /* TX: DATA = out pin, CLK = side-set */
    uint off = pio_add_program(lpio, &link_tx_program);
    sm_link = pio_claim_unused_sm(lpio, true);
    pio_sm_config c = link_tx_program_get_default_config(off);
    sm_config_set_out_pins(&c, PIN_LINK_DATA, 1);
    sm_config_set_sideset_pins(&c, PIN_LINK_CLK);
    sm_config_set_out_shift(&c, false, true, 32);            /* MSB first, autopull */
    sm_config_set_clkdiv(&c, (float)clock_get_hz(clk_sys) / (2.0f * LINK_BIT_HZ));
    pio_gpio_init(lpio, PIN_LINK_DATA); pio_gpio_init(lpio, PIN_LINK_CLK);
    pio_sm_set_consecutive_pindirs(lpio, sm_link, PIN_LINK_DATA, 1, true);
    pio_sm_set_consecutive_pindirs(lpio, sm_link, PIN_LINK_CLK, 1, true);
    pio_sm_init(lpio, sm_link, off, &c);
    pio_sm_set_enabled(lpio, sm_link, true);
    /* RX: PIO UART on LINK_RX */
    uint off2 = pio_add_program(lpio, &uart_rx_program);
    sm_ret = pio_claim_unused_sm(lpio, true);
    pio_sm_config r = uart_rx_program_get_default_config(off2);
    sm_config_set_in_pins(&r, PIN_LINK_RX); sm_config_set_jmp_pin(&r, PIN_LINK_RX);
    sm_config_set_in_shift(&r, true, false, 32);
    sm_config_set_fifo_join(&r, PIO_FIFO_JOIN_RX);
    sm_config_set_clkdiv(&r, (float)clock_get_hz(clk_sys) / (8.0f * RET_BAUD));
    pio_gpio_init(lpio, PIN_LINK_RX); gpio_pull_up(PIN_LINK_RX);
    pio_sm_set_consecutive_pindirs(lpio, sm_ret, PIN_LINK_RX, 1, false);
    pio_sm_init(lpio, sm_ret, off2, &r);
    pio_sm_set_enabled(lpio, sm_ret, true);
}
void maplink_send(uint32_t frame) { pio_sm_put_blocking(lpio, sm_link, frame); }
bool maplink_send_try(uint32_t frame) { if (pio_sm_is_tx_fifo_full(lpio, sm_link)) return false; pio_sm_put(lpio, sm_link, frame); return true; }
int maplink_recv_byte(uint32_t timeout_us) {
    absolute_time_t t = make_timeout_time_us(timeout_us);
    while (pio_sm_is_rx_fifo_empty(lpio, sm_ret)) { if (time_reached(t)) return -1; }
    return (int)((pio_sm_get(lpio, sm_ret) >> 24) & 0xFF);
}
bool maplink_wait_ack(int expect, uint32_t timeout_us) {
    absolute_time_t t = make_timeout_time_us(timeout_us);
    for (;;) { int b = maplink_recv_byte(timeout_us); if (b < 0 || time_reached(t)) return false; if (b == expect) return true; }
}
#endif

#if FC_ROLE_CHR
void maplink_init(void) {
    pio_set_gpio_base(lpio, 16);
    uint off = pio_add_program(lpio, &link_rx_program);
    sm_link = pio_claim_unused_sm(lpio, true);
    pio_sm_config c = link_rx_program_get_default_config(off);
    sm_config_set_in_pins(&c, PIN_LINK_CLK);                 /* pin0 = CLK, pin1 = DATA (adjacent GPIOs) */
    sm_config_set_in_shift(&c, false, true, 32);             /* shift left: 2 bits per clock, autopush every 16 clocks (2 words per frame) */
    sm_config_set_fifo_join(&c, PIO_FIFO_JOIN_RX);
    pio_gpio_init(lpio, PIN_LINK_CLK); pio_gpio_init(lpio, PIN_LINK_DATA);
    pio_sm_set_consecutive_pindirs(lpio, sm_link, PIN_LINK_CLK, 2, false);
    pio_sm_init(lpio, sm_link, off, &c);
    pio_sm_set_enabled(lpio, sm_link, true);
    uint off2 = pio_add_program(lpio, &uart_tx_program);
    sm_ret = pio_claim_unused_sm(lpio, true);
    pio_sm_config t = uart_tx_program_get_default_config(off2);
    sm_config_set_out_pins(&t, PIN_LINK_TX, 1); sm_config_set_sideset_pins(&t, PIN_LINK_TX);
    sm_config_set_out_shift(&t, true, false, 32);
    sm_config_set_fifo_join(&t, PIO_FIFO_JOIN_TX);
    sm_config_set_clkdiv(&t, (float)clock_get_hz(clk_sys) / (8.0f * RET_BAUD));
    pio_gpio_init(lpio, PIN_LINK_TX);
    pio_sm_set_pins_with_mask64(lpio, sm_ret, 1ull << PIN_LINK_TX, 1ull << PIN_LINK_TX);
    pio_sm_set_consecutive_pindirs(lpio, sm_ret, PIN_LINK_TX, 1, true);
    pio_sm_init(lpio, sm_ret, off2, &t);
    pio_sm_set_enabled(lpio, sm_ret, true);
}
/* The RX program shifts 2 bits per clock (CLK=1, DATA): 32 clocks fill a 64-bit ISR window, pushed as two words.
 * We rebuild the 32 data bits from the odd bit positions of the two words. */
bool maplink_poll(uint32_t *frame) {
    static uint32_t half; static int have;
    while (!pio_sm_is_rx_fifo_empty(lpio, sm_link)) {
        uint32_t w = pio_sm_get(lpio, sm_link);
        uint32_t bits = 0;                                   /* extract DATA bits (bit1 of each 2-bit group) */
        for (int i = 0; i < 16; i++) bits = (bits << 1) | ((w >> (31 - 2 * i - 0)) & 1);
        if (!have) { half = bits; have = 1; continue; }
        have = 0;
        uint32_t f = (half << 16) | bits;
        if ((f >> 28) != LINK_TAG) {                         /* lost alignment: restart the SM and tell U1 */
            pio_sm_set_enabled(lpio, sm_link, false); pio_sm_clear_fifos(lpio, sm_link); pio_sm_restart(lpio, sm_link); pio_sm_set_enabled(lpio, sm_link, true);
            maplink_reply(LINK_R_ERROR); continue;
        }
        *frame = f; return true;
    }
    return false;
}
void maplink_reply(uint8_t b) { pio_sm_put_blocking(lpio, sm_ret, b); }
#endif
