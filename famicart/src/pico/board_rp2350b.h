/* famicart rev C: bare RP2350B, all 48 GPIO used, console signals connected directly (RP2350 GPIO are 5 V tolerant).
 *
 *  GPIO0-14  CPU A0-A14      GPIO15-22 CPU D0-D7      GPIO23 R/W   GPIO24 M2   GPIO25 /ROMSEL   GPIO26 /IRQ (emulated open drain)
 *  GPIO27    CIRAM /CE       GPIO28/29 UART0 TX/RX -> XIAO RP2040 (audio coprocessor)
 *  GPIO30-37 PPU shared port (A0-7 via 74LVC541 while PPU_SEL=0, D0-7 via 74LVC245 while PPU_SEL=1)
 *  GPIO38-43 PPU A8-A13      GPIO44 /PPUACC (= /RD & /WR)   GPIO45 PPU /RD   GPIO46 PPU_SEL   GPIO47 CIRAM A10
 */
#pragma once
#define FC_BUS_CAPABLE        1
#define FC_BUS_DIRECT         1      /* CPU bus wired directly: one 26-bit PIO capture per M2 */
#define FC_AUDIO_REMOTE       1      /* expansion-audio registers are streamed to the XIAO over UART0 */

#define PIN_CPU_BASE          0      /* GPIO0..25: A0-14 (0-14), D0-7 (15-22), R/W 23, M2 24, /ROMSEL 25 */
#define PIN_CPU_DATA_BASE     15
#define PIN_CPU_RW            23
#define PIN_CPU_M2            24
#define PIN_CPU_ROMSEL        25
#define PIN_IRQ               26
#define PIN_CIRAM_CE          27
#define PIN_UART_TX           28
#define PIN_UART_RX           29
#define PIN_PPU_PORT_BASE     30     /* GPIO30..45 captured in one go: port(8) A8-13(6) /PPUACC /RD */
#define PIN_PPU_AHI_BASE      38
#define PIN_PPU_ACC           44
#define PIN_PPU_RD            45
#define PIN_PPU_SEL           46
#define PIN_CIRAM_A10         47
#define PIN_AUDIO_PWM         (-1)   /* audio is produced by the XIAO */

#define FC_SYS_CLOCK_KHZ      300000 /* RP2350 overclock; 150 MHz nominal also works with less margin */
#define FC_FLASH_ROM_SLOT     0x00100000u   /* 1 MiB into the 16 MiB flash */
#define FC_FLASH_ROM_SLOT_MAX 0x00F00000u   /* 15 MiB: room for a ROM library (phase 3) */
