/* famicart rev D, U2 "CHR mapper" (RP2350B): snoops the local PPU bus, drives CHR flash/RAM bank lines,
 * CHR ROM/RAM select, CIRAM A10 and the 4-screen enable; runs the PPU-side mapper hooks (MMC2/MMC4 latches,
 * MMC3 A12 counter, MMC5 scanline counter) and raises /IRQ_B. State arrives from U1 over the 2-wire link. */
#pragma once
#define FC_BUS_CAPABLE        0
#define FC_VIRTUAL_ROM        1
#define FC_ROLE_CHR           1

#define PIN_PPU_BASE          0      /* GPIO0-13 = PA0-13 */
#define PIN_PPU_NRD           14
#define PIN_PPU_NWR           15
#define PIN_CHR_BANK_BASE     16     /* GPIO16-31 = CHR flash / CHR RAM A10-A25 */
#define PIN_CHR_BANK_BITS     16
#define PIN_CHR_SEL           32     /* 0 = CHR flash, 1 = CHR RAM */
#define PIN_NFOURSCR          33     /* 0 = CIRAM disabled (4-screen / mapper nametables in CHR RAM) */
#define PIN_CIRAM_A10         34
#define PIN_LED               35
#define PIN_CHR_NWE           36
#define PIN_LINK_CLK          37     /* <- U1 */
#define PIN_LINK_DATA         38     /* <- U1 */
#define PIN_LINK_TX           39     /* -> U1 (PIO UART, 2 Mbaud) */
#define PIN_IRQ               40
#define PIN_NBRIDGE           41     /* low: CPU<->PPU data bridge enabled (flash programming / read-back) */
#define PIN_BRIDGE_DIR        42     /* 1: CPU->PPU, 0: PPU->CPU */
#define PIN_CHR_RYBY          43     /* CHR flash RY/BY# */
#define PIN_AUDIO_PWM         (-1)
#define PIN_CIRAM_CE          (-1)
#define PIN_UART_TX           (-1)

#define FC_SYS_CLOCK_KHZ      150000
#define FC_FLASH_ROM_SLOT     0x00100000u
#define FC_FLASH_ROM_SLOT_MAX 0x00010000u
