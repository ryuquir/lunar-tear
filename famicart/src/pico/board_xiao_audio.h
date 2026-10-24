/* Seeed XIAO RP2040 as the rev C audio coprocessor: receives expansion-audio register writes from the RP2350B
 * over UART0 and renders them to PWM. Also drives the onboard RGB LED as a status indicator. */
#pragma once
#define FC_BUS_CAPABLE        0
#define FC_AUDIO_COPROCESSOR  1
#define PIN_UART_TX           0      /* D6 -> RP2350B GPIO29 (RX) */
#define PIN_UART_RX           1      /* D7 <- RP2350B GPIO28 (TX) */
#define PIN_AUDIO_PWM         26     /* D0 -> R1/C1 ... -> cart pin 46 */
#define PIN_LED_R             17
#define PIN_LED_G             16
#define PIN_LED_B             25
#define PIN_IRQ               (-1)
#define PIN_CIRAM_A10         (-1)
#define PIN_CIRAM_CE          (-1)
#define FC_SYS_CLOCK_KHZ      200000
#define FC_FLASH_ROM_SLOT     0x00040000u
#define FC_FLASH_ROM_SLOT_MAX 0x00100000u
