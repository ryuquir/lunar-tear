/* UART link between the main MCU and the XIAO audio coprocessor (rev C).
 * Frame (4 bytes): 0xF0|chip, addr_hi, addr_lo, value.   chip 0 = control (addr 0: reset, 1: master volume, 2: LED rgb565 hi/lo) */
#pragma once
#include <stdint.h>
#include <stdbool.h>
#define AUDIO_LINK_BAUD 3000000
void audio_link_init(void);                                   /* both sides */
void audio_link_send(uint8_t chip, uint16_t addr, uint8_t v);  /* main MCU side (non-blocking, drops when the FIFO is full) */
bool audio_link_poll(uint8_t *chip, uint16_t *addr, uint8_t *v); /* coprocessor side: returns one decoded frame if available */
