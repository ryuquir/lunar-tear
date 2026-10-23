/* Raspberry Pi Pico / Pico 2 wiring (26 GPIO, all that the module exposes). See docs/04_hardware.md.
 *
 *  Cartridge CPU bus  -> 3x 74LVC541 (CTRL: R/W,/ROMSEL | A8-14 | A0-7) + 1x 74LVC245 (D0-7, DIR = R/W) -> 8-bit CPU_PORT
 *                        The CTRL buffer is enabled in the idle state (decoder output Y0), so R/W and /ROMSEL are
 *                        readable on the port without dedicated GPIOs.
 *  Cartridge PPU bus  -> 2x 74LVC541 (A0-7 | A8-13+/RD+/WR) + 1x 74LVC245 (D0-7, DIR = /RD) -> 8-bit PPU_PORT
 *  Buffer /OE lines   <- 74HC139 (dual 2-to-4 decoder), one half per port: Y0 ctrl/idle, Y1 A-lo, Y2 A-hi, Y3 data
 *  Strobes            <- 74LVC1G17 (M2 level shift), 74LVC1G08 (/PPUACC = PPU /RD AND PPU /WR)
 *  /IRQ               -> 74LVC1G07 open-drain buffer (GPIO low = /IRQ asserted)
 */
#pragma once
#define FC_BUS_CAPABLE        1

#define PIN_CPU_PORT_BASE     0     /* GP0..GP7  shared CPU ctrl/address/data port */
#define PIN_PPU_PORT_BASE     8     /* GP8..GP15 shared PPU address/data port */
#define PIN_PPU_ACC           16    /* GP16 /PPUACC (= /RD & /WR), 3.3 V from 74LVC1G08 */
#define PIN_CPU_M2            17    /* GP17 M2, 3.3 V from 74LVC1G17 */
#define PIN_CPU_SEL_BASE      18    /* GP18,GP19 -> 74HC139 A: 0 ctrl(idle), 1 /OE A-lo, 2 /OE A-hi, 3 /OE data */
#define PIN_PPU_SEL_BASE      20    /* GP20,GP21 -> 74HC139 B: 0 idle, 1 /OE A-lo, 2 /OE A-hi, 3 /OE data */
#define PIN_IRQ               22    /* GP22 -> 74LVC1G07 -> /IRQ (drive low to assert) */
#define PIN_AUDIO_PWM         26    /* GP26 -> RC filter -> mix into cart pin 46 */
#define PIN_CIRAM_A10         27    /* GP27 */
#define PIN_CIRAM_CE          28    /* GP28 CIRAM /CE */

/* Bit layout inside the CPU "CTRL" buffer (visible while SEL=0): D0 = R/W, D1 = /ROMSEL, D2-D7 = 0 */
#define CPU_CTRL_RW_BIT       0
#define CPU_CTRL_ROMSEL_BIT   1
/* CPU "A-hi" buffer: D0-D6 = A8-A14, D7 = 0 */
/* Bit layout inside the PPU "A-hi" buffer: D0-D5 = A8-A13, D6 = /RD, D7 = /WR */
#define PPU_HI_RD_BIT         6
#define PPU_HI_WR_BIT         7

#define FC_SYS_CLOCK_KHZ      252000   /* 2x 126 MHz; flash divider stays 2 -> 126 MHz QSPI, within W25Q spec */
#define FC_FLASH_ROM_SLOT     0x00040000u   /* 256K into flash: [profile 256B][.nes image] */
#define FC_FLASH_ROM_SLOT_MAX 0x001C0000u   /* up to 1.75 MiB on 2 MiB parts */
