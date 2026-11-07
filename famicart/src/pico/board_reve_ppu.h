/* famicart rev E, U2: Raspberry Pi Pico 2 on the PPU bus.
 *   GP0-13  PPU A0-A13 (1 k)   GP14-21 PPU D0-D7 (1 k)   GP22 PPU /RD (1 k)
 *   GP26    CIRAM /CE (100 k to /A13 as power-up default)   GP27 CIRAM A10   GP28 LINK   GP25 LED */
#pragma once
#define FC_BUS_CAPABLE        0
#define FC_REVE               1
#define PIN_PPU_A_BASE        0
#define PIN_PPU_D_BASE        14
#define PIN_PPU_RD            22
#define PIN_CIRAM_CE          26
#define PIN_CIRAM_A10         27
#define PIN_LINK              28
#define PIN_LED               25
#define PIN_AUDIO_PWM         (-1)
#define PIN_UART_TX           (-1)
#define FC_SYS_CLOCK_KHZ      240000
#define FC_FLASH_CHR          0x00080000u  /* CHR cache for games whose CHR is larger than the SRAM pool */
#define FC_FLASH_END          0x00400000u
#define FC_FLASH_ROM_SLOT     FC_FLASH_CHR
