/* pico-sdk board header for famicart rev H: all eight RP2350B (U1-U6, U8, U9; docs/13_rev_h_plan.md). Every chip has
 * the same parts around it: RP2350B QFN-80 (silicon A4), its own W25Q128JVSIQ (16 MB) on QSPI CS0, a 12 MHz crystal
 * TXM12M0004322CBCDO00T (not the Raspberry Pi part) with 12 pF x2 and 1k in XOUT, DVDD from the board's common 1.1 V
 * (the on-chip regulator is unused: VREG_FB to GND, VREG_LX open). The chip's own pins come from
 * src/revh/pins_u<N>.h (generated from tools/pcb/design_revh.py), not from here.
 *
 * Written from the SDK's boards/pico2.h and boards/pimoroni_pga2350.h (RP2350B with 16 MB flash), but without
 * including them: pico2.h also defines PICO_DEFAULT_LED_PIN 25, UART 0 / 1, I2C 4 / 5, SPI 16-19, PICO_SMPS_MODE_PIN 23,
 * PICO_VBUS_PIN 24 and PICO_VSYS_PIN 29, and on the chips that use them every one of those GPIOs carries something
 * else on rev H (docs/13 "移植の一覧"): 25 is the hub's VSEL (core voltage) and the raw /ROMSEL of U1 / U3 / U4, 24 the
 * hub's nRST and a raw strobe elsewhere, 23 the raw R/W of U1 / U4, 0 / 1 LINK_F / SD_CD on the hub and bus address
 * lines elsewhere, 4 / 5 SD_DAT0 / 1, 29 WLINK, audio PWM or XLINK-H1 (hub). So no default pins at all: code that needs
 * a pin takes it from pins_u<N>.h.
 *
 * NOTE: THIS HEADER IS ALSO INCLUDED BY ASSEMBLER SO SHOULD ONLY CONSIST OF PREPROCESSOR DIRECTIVES. */
#ifndef _BOARDS_FAMICART_REVH_H
#define _BOARDS_FAMICART_REVH_H

pico_board_cmake_set(PICO_PLATFORM, rp2350)

// For board detection
#define FAMICART_REVH

// --- RP2350 VARIANT ---
// QFN-80: GPIO0-47, ADC0-7 on GPIO40-47 (ADC_BASE_PIN 40). With PICO_RP2350A 1 (pico2.h) GPIO32-47 do not exist for
// the SDK and the ADC starts at GPIO26.
#define PICO_RP2350A 0

// --- UART / I2C / SPI / LED ---
// None: see above. stdio over UART is never enabled for rev H (the hub's stdio is USB CDC; the others have no console).
// The USB-reset BOOTSEL activity LED is set per build in CMakeLists.txt (hub only, its own LED).

// --- CRYSTAL ---
// 12 MHz, as the SDK assumes (XOSC_HZ default): PLL settings, USB 48 MHz and the boot ROM's USB boot all expect it.
// Start-up delay: the SDK waits for XOSC STATUS_STABLE, which counts STARTUP.DELAY x 256 cycles OF THE CRYSTAL, so a
// crystal that starts late only makes the wait start late; the delay itself covers the amplitude build-up after the
// first edges. The datasheet (8.2.4) finds 1 ms enough for the Raspberry Pi crystal; the SDK's default since 2.x is
// 6 ms. This crystal is not that part (docs/13 "クロック": 5 % less oscillation margin, half the drive level), so the
// default is kept on purpose and written out here: 6 x 1 ms is six times the figure for the recommended part, and every
// extra millisecond delays all eight chips (U1 must answer the CPU's reset vector about 17 ms after power-on; docs/13
// "電源投入から最初の読み出しまで" starts its first PIO before the clock set-up anyway). Bring-up step 3 measures the
// start-up time; raise this if XOUT is still growing at 6 ms. Guarded like the SDK's own board headers, so a build
// can try another value (-D on the compiler command line or target_compile_definitions) without editing this file.
#ifndef PICO_XOSC_STARTUP_DELAY_MULTIPLIER
#define PICO_XOSC_STARTUP_DELAY_MULTIPLIER 6
#endif

// --- CORE VOLTAGE ---
// DVDD comes from the board's 1.1 V converter (1.092 V, or about 1.122 V with VSEL); the on-chip regulator has no
// inductor and must go to high impedance at start (src/revh/revh_start.c, docs/13 "コア電圧の切り替えの手順"). Nothing
// may write its voltage: the SDK's clock set-up only does so when this is 1 (its default on RP2350 is already 0 at
// 150 MHz; pinned so that a raised SYS_CLK_HZ cannot turn it on). The rev H CMake target also wraps
// vreg_set_voltage() so that a call anywhere fails to link.
#define SYS_CLK_VREG_VOLTAGE_AUTO_ADJUST 0

// --- FLASH ---
// W25Q128JVSIQ: 16 MB, the most one chip select addresses. The boot ROM scans for the image with EBh quad read at SCK
// divisor 3 first (datasheet table 463) and leaves that mode in place; the SDK runs from it (PICO_EMBED_XIP_SETUP 0).
// The W25Q128JV takes EBh with the continuous-read mode bits and 4 dummy clocks like the W25Q080, and Winbond's -IQ
// ordering code ships with QE = 1, so the W25Q080 boot stage 2 should find nothing to write in the status registers
// (if QE were 0 it would write it, the boot ROM alone would fall back to BBh / 0Bh). The stage 2 is only used when a
// build sets PICO_EMBED_XIP_SETUP 1.
#define PICO_BOOT_STAGE2_CHOOSE_W25Q080 1
// Divisor 3: the same SCK as the boot ROM's mode (50 MHz at 150 MHz). Only the divisor matches: embedding the stage 2
// would also switch CS0 to EBh continuous-read mode (mode bits A0h, later reads without the command prefix) with
// PICO_FLASH_SPI_RXDELAY 2 (boot2_w25q080.S), where every mode the boot ROM sets keeps the 8-bit serial command
// prefix with the mode bits at 0 (datasheet 5.4.8.14) and its RXDELAY is not stated. Validate that on the hub's
// two-flash bus (U16, U7 share SCLK / SD0-3; docs/13 rule 13: the hub's RXDELAY is found by scanning) before a build
// sets PICO_EMBED_XIP_SETUP 1. Rev E already runs its flash at divisor 3 at 240 MHz.
#ifndef PICO_FLASH_SPI_CLKDIV
#define PICO_FLASH_SPI_CLKDIV 3
#endif

pico_board_cmake_set_default(PICO_FLASH_SIZE_BYTES, (16 * 1024 * 1024))
#ifndef PICO_FLASH_SIZE_BYTES
#define PICO_FLASH_SIZE_BYTES (16 * 1024 * 1024)
#endif

// Silicon A4 (LCSC C42415655). A2 support (the SDK's default, as in pico2.h) only adds the UF2's absolute block for
// erratum E10 and workarounds in libraries rev H does not use (PSRAM, BTstack); harmless on A4.
pico_board_cmake_set_default(PICO_RP2350_A2_SUPPORTED, 1)
#ifndef PICO_RP2350_A2_SUPPORTED
#define PICO_RP2350_A2_SUPPORTED 1
#endif

#endif
