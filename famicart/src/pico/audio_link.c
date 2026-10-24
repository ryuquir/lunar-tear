#include "audio_link.h"
#include "board.h"
#include "pico/stdlib.h"
#include "hardware/uart.h"
#include "hardware/gpio.h"

#if defined(PIN_UART_TX) && PIN_UART_TX >= 0
#define LINK_UART uart0
void audio_link_init(void) {
    uart_init(LINK_UART, AUDIO_LINK_BAUD);
    gpio_set_function(PIN_UART_TX, GPIO_FUNC_UART); gpio_set_function(PIN_UART_RX, GPIO_FUNC_UART);
    uart_set_format(LINK_UART, 8, 1, UART_PARITY_NONE); uart_set_fifo_enabled(LINK_UART, true);
}
void audio_link_send(uint8_t chip, uint16_t addr, uint8_t v) {
    if (!uart_is_writable(LINK_UART)) return;      /* called from the bus ISR: never block */
    uart_get_hw(LINK_UART)->dr = 0xF0u | (chip & 7);
    uart_get_hw(LINK_UART)->dr = (uint8_t)(addr >> 8);
    uart_get_hw(LINK_UART)->dr = (uint8_t)addr;
    uart_get_hw(LINK_UART)->dr = v;
}
bool audio_link_poll(uint8_t *chip, uint16_t *addr, uint8_t *v) {
    static uint8_t buf[4]; static unsigned n;
    while (uart_is_readable(LINK_UART)) {
        uint8_t b = (uint8_t)uart_get_hw(LINK_UART)->dr;
        if (n == 0 && (b & 0xF8) != 0xF0) continue;        /* resync on a header byte */
        buf[n++] = b;
        if (n == 4) { n = 0; *chip = buf[0] & 7; *addr = (uint16_t)(buf[1] << 8 | buf[2]); *v = buf[3]; return true; }
    }
    return false;
}
#else
void audio_link_init(void) {}
void audio_link_send(uint8_t chip, uint16_t addr, uint8_t v) { (void)chip; (void)addr; (void)v; }
bool audio_link_poll(uint8_t *chip, uint16_t *addr, uint8_t *v) { (void)chip; (void)addr; (void)v; return false; }
#endif
