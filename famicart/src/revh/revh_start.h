/* famicart rev H: start-up shared by every program on the eight RP2350B (docs/13_rev_h_plan.md "コア電圧の切り替えの手順",
 * "ファミコンの電源だけで動かすための決まり"). Call revh_start() first in main(). In U8 / U9 builds (FC_REVH_CHIP 8 / 9)
 * revh_start.c also replaces the SDK's runtime_init_clocks(): those chips start at 12 MHz from the crystal and never
 * start a PLL by themselves (docs/13 rule 9). */
#pragma once
#include <stdbool.h>
#include <stdint.h>

#define REVH_SYS_CLK_MAX_HZ 150000000u     /* start-up rule: no chip above 150 MHz until the hub allows it */

/* VREG to high impedance (the docs/13 procedure), then clk_sys checked against REVH_SYS_CLK_MAX_HZ (lowered, never
 * raised). Touches no GPIO. The VREG step has already run once from the runtime init (before the clocks), so here it
 * only confirms it. */
void revh_start(void);

/* The docs/13 procedure: unlock VREG_CTRL (password 0x5AFE), wait while an update is in progress, set HIZ in VREG.
 * Both writes set bits through the atomic set alias, as the SDK's own powman / vreg code does: a plain write of
 * 0x5AFE<<16 | UNLOCK would also clear VREG_CTRL.RST_N (which returns the regulator to its start-up settings) and
 * HT_TH, and a plain write to VREG would set VSEL to 0.55 V. Idempotent. */
void revh_vreg_hiz(void);
bool revh_vreg_is_hiz(void);
uint32_t revh_vreg_raw(void);              /* POWMAN VREG (HIZ = bit 1, VSEL = bits 8:4, UPDATE_IN_PROGRESS = bit 15) */

/* A pin on a net that reaches the console (REVH_CONSOLE_MASK of pins_u<N>.h) for a program that does not serve the bus:
 * function NULL, pad output disabled, input buffer on, both pulls off, then the pad isolation released (until then the
 * pad keeps its reset state: pull-down on). */
void revh_pin_float(unsigned gpio);
void revh_pins_float(uint64_t mask);

/* Standby clocks (docs/13: U8 / U9 wait at 12 MHz with the PLLs stopped; unused chips at 12-48 MHz): clk_sys and
 * clk_peri from the 12 MHz crystal, clk_usb / clk_adc / clk_hstx stopped, both PLLs powered down. The timer keeps its
 * 1 us tick (it runs from clk_ref, already the crystal). Not for the hub: its USB and ADC need PLL_USB. */
void revh_clock_standby(void);
