/* famicart rev E, U3: Seeed XIAO RP2350 "special chip" -- IRQ timing and expansion audio.
 *   D0 = GPIO26 LINK   D1 = GPIO27 audio PWM (RC to AUDIO_OUT)   D2 = GPIO28 IRQ gate (2N7002 -> /IRQ, high = assert)
 *   D3 = GPIO5 M2 (1 k)   D4 = GPIO6 PPU A12   D5 = GPIO7 PPU A13   D6 = GPIO0 PPU /RD */
#pragma once
#define FC_BUS_CAPABLE        0
#define FC_REVE               1
#define PIN_LINK              26
#define PIN_AUDIO_PWM         27
#define PIN_IRQ_GATE          28
#define PIN_M2                5
#define PIN_PA12              6
#define PIN_PA13              7
#define PIN_PPU_RD            0
#define PIN_LED               25
#define PIN_UART_TX           (-1)
#define PIN_CIRAM_A10         (-1)
#define PIN_CIRAM_CE          (-1)
#define FC_SYS_CLOCK_KHZ      240000
#define FC_FLASH_ROM_SLOT     0x00100000u
