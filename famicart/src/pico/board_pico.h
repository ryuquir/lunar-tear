/* Raspberry Pi Pico / Pico 2 wiring (27 GPIO). See docs/04_hardware.md for the schematic.
 *
 *  Cartridge CPU bus  -> 2x 74LVC541 (A0-7 | A8-14+R/W)  + 1x 74LVC245 (D0-7, DIR = R/W)  -> 8-bit port CPU_PORT
 *  Cartridge PPU bus  -> 2x 74LVC541 (A0-7 | A8-13+/RD+/WR) + 1x 74LVC245 (D0-7, DIR = /RD) -> 8-bit port PPU_PORT
 *  Buffer /OE lines   <- 74HC139 (dual 2-to-4 decoder), one half per port, driven by 2 select pins each
 *  PPU access strobe  <- 74LVC1G08: /PPUACC = PPU /RD AND PPU /WR
 */
#pragma once
#define FC_BUS_CAPABLE        1

#define PIN_CPU_PORT_BASE     0     /* GP0..GP7  shared CPU address/data port */
#define PIN_CPU_ROMSEL        8     /* GP8  /ROMSEL (read as bit 8 together with the port) */
#define PIN_PPU_PORT_BASE     9     /* GP9..GP16 shared PPU address/data port */
#define PIN_PPU_ACC           17    /* GP17 /PPUACC (= /RD & /WR) */
#define PIN_CPU_SEL_BASE      18    /* GP18,GP19 -> 74HC139 A: 0 idle, 1 /OE A-lo, 2 /OE A-hi, 3 /OE data */
#define PIN_PPU_SEL_BASE      20    /* GP20,GP21 -> 74HC139 B: same encoding */
#define PIN_CPU_M2            22    /* GP22 M2 */
#define PIN_AUDIO_PWM         25    /* GP25 (also the Pico LED) -> RC filter -> mix into cart pin 46 */
#define PIN_IRQ               26    /* GP26 /IRQ, open drain (low or hi-Z) */
#define PIN_CIRAM_A10         27    /* GP27 */
#define PIN_CIRAM_CE          28    /* GP28 CIRAM /CE */

/* Bit layout inside the CPU "A-hi" buffer: D0-D6 = A8-A14, D7 = R/W */
#define CPU_HI_RW_BIT         7
/* Bit layout inside the PPU "A-hi" buffer: D0-D5 = A8-A13, D6 = /RD, D7 = /WR */
#define PPU_HI_RD_BIT         6
#define PPU_HI_WR_BIT         7

#define FC_SYS_CLOCK_KHZ      252000   /* 2x 126 MHz; flash divider stays 2 -> 126 MHz QSPI, within W25Q spec */
#define FC_FLASH_ROM_SLOT     0x00040000u   /* 256K into flash: [profile 256B][.nes image] */
#define FC_FLASH_ROM_SLOT_MAX 0x001C0000u   /* up to 1.75 MiB on 2 MiB parts */
