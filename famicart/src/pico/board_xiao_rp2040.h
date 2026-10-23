/* Seeed Studio XIAO RP2040: 11 usable GPIO (GP0-4, GP6, GP7, GP26-29) + NeoPixel (GP12/power GP11).
 * The Famicom cartridge bus needs >= 27 GPIO even with external buffers, so this board
 * cannot drive the bus. This profile builds the same firmware without the bus front-end:
 * ROM detection, mapper engine self-test and expansion-audio synthesis run and report
 * over USB-CDC, which is useful for bench-testing the audio mix and the ROM slot format. */
#pragma once
#define FC_BUS_CAPABLE        0
#define PIN_AUDIO_PWM         26    /* D0 (A0) */
#define PIN_IRQ               27
#define PIN_CIRAM_A10         28
#define PIN_CIRAM_CE          29
#define PIN_CPU_PORT_BASE     0
#define PIN_PPU_PORT_BASE     0
#define PIN_PPU_ACC           0
#define PIN_CPU_SEL_BASE      0
#define PIN_PPU_SEL_BASE      0
#define PIN_CPU_M2            0
#define CPU_CTRL_RW_BIT       0
#define CPU_CTRL_ROMSEL_BIT   1
#define PPU_HI_RD_BIT         6
#define PPU_HI_WR_BIT         7
#define FC_SYS_CLOCK_KHZ      200000
#define FC_FLASH_ROM_SLOT     0x00040000u
#define FC_FLASH_ROM_SLOT_MAX 0x001C0000u
