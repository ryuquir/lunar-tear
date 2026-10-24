/* pico-sdk board header for the famicart rev C main MCU (bare RP2350B, 16 MB W25Q128 flash, 12 MHz crystal). */
#ifndef _BOARDS_FAMICART_RP2350B_H
#define _BOARDS_FAMICART_RP2350B_H
#include "boards/pico2.h"
#undef PICO_RP2350A
#define PICO_RP2350A 0                      /* QFN-80: 48 GPIO */
#undef PICO_DEFAULT_LED_PIN                 /* no LED on the main MCU (status via the XIAO) */
#undef PICO_DEFAULT_UART_TX_PIN
#undef PICO_DEFAULT_UART_RX_PIN
#define PICO_DEFAULT_UART 0
#define PICO_DEFAULT_UART_TX_PIN 28         /* -> XIAO RX (link to the audio coprocessor) */
#define PICO_DEFAULT_UART_RX_PIN 29
#undef PICO_FLASH_SIZE_BYTES
#define PICO_FLASH_SIZE_BYTES (16 * 1024 * 1024)
#endif
