/* rev E link hardware: PIO half-duplex UART on one pin (see reve.pio and core/reve/reve_link.h). */
#pragma once
#include <stdint.h>
#include <stdbool.h>
#include "hardware/pio.h"
#define RL_BAUD 12500000u
void rlhw_init(PIO pio, unsigned pin);
bool rlhw_tx_try(uint16_t sym);            /* false when the TX FIFO is full */
void rlhw_tx(uint16_t sym);
bool rlhw_tx_idle(void);                   /* FIFO empty and the last symbol has left the pin */
int  rlhw_rx(void);                        /* next received symbol that is not our own echo, or -1 */
int  rlhw_rx_wait(uint32_t timeout_us);
void rlhw_rx_reset(void);                   /* line idle: drop everything received so far (echoes included) */
void rlhw_rx_irq(void (*handler)(void));    /* call handler (on this core) whenever symbols arrive */
