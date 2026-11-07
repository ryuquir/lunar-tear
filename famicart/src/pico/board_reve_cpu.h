/* famicart rev E, U1: Raspberry Pi Pico 2 on the CPU bus (see docs/06_rev_e_plan.md).
 *   GP0-14  CPU A0-A14 (1 k)      GP15-22 CPU D0-D7 (1 k, 5 V tolerant)
 *   GP26    /ROMSEL (1k/2.2k divider)   GP27 /WS = NOT(M2 AND NOT R/W) (divider)   GP28 LINK   GP25 LED */
#pragma once
#define FC_BUS_CAPABLE        0
#define FC_REVE               1
#define PIN_CPU_A_BASE        0
#define PIN_CPU_D_BASE        15
#define PIN_ROMSEL            26
#define PIN_WS                27
#define PIN_LINK              28
#define PIN_LED               25
#define PIN_AUDIO_PWM         (-1)
#define PIN_UART_TX           (-1)
#define PIN_CIRAM_A10         (-1)
#define PIN_CIRAM_CE          (-1)
#define FC_SYS_CLOCK_KHZ      240000
#define FC_WCAP_DELAY_NS      220          /* /WS fall -> sample write data */
#define FC_DWELL_NS           300          /* minimum address dwell of a confirmed read */
#define FC_FLASH_LIB          0x00080000u  /* library index (64 KB) */
#define FC_FLASH_DATA         0x00090000u  /* ROM images up to the end of the 4 MB flash */
#define FC_FLASH_END          0x00400000u
#define FC_FLASH_ROM_SLOT     FC_FLASH_LIB
