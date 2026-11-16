/* famicart rev H: start-up shared by every program on the eight RP2350B (see revh_start.h).
 *
 * Core voltage: DVDD comes from the board's 1.1 V converter for all eight chips; the on-chip regulator has no inductor
 * (VREG_LX open, VREG_FB grounded) and must go to high impedance right after start (docs/13 "コア電圧の切り替えの手順";
 * datasheet 6.3.1.3 / 6.3.7: safe, about 400 uA until it is shut down). Nothing may set its voltage or use a low-power
 * mode. What in the SDK could touch it, checked against pico-sdk 2.3.1:
 *   - runtime_init_clocks() calls vreg_set_voltage() only when SYS_CLK_VREG_VOLTAGE_AUTO_ADJUST is 1. hardware/clocks.h
 *     makes that 1 for RP2040 at 200 MHz only; the board header pins it to 0 and the check below stops the build
 *     otherwise. set_sys_clock_*() and clock_configure() never touch the regulator.
 *   - pico_low_power writes VREG_CTRL; rev H does not link it.
 *   - the rev H CMake target links with --wrap=vreg_set_voltage / vreg_disable_voltage_limit and defines no wrapper,
 *     so any call to either fails to link.
 * Never run a rev H build on a board whose DVDD comes from the on-chip regulator (e.g. a Pico 2): there, HIZ resets
 * the chip (datasheet 6.3.1.3) and the program starts over for ever (hold BOOTSEL to recover). */
#include "revh_start.h"
#include "pico.h"
#include "pico/runtime_init.h"
#include "hardware/clocks.h"
#include "hardware/pll.h"
#include "hardware/ticks.h"
#include "hardware/xosc.h"
#include "hardware/gpio.h"
#include "hardware/structs/powman.h"
#include "hardware/structs/pads_bank0.h"
#include "hardware/structs/io_bank0.h"
#include "hardware/regs/powman.h"

#if SYS_CLK_VREG_VOLTAGE_AUTO_ADJUST
#error "rev H: the SDK must not set the core voltage (SYS_CLK_VREG_VOLTAGE_AUTO_ADJUST must be 0, boards/famicart_revh.h)"
#endif
#if SYS_CLK_HZ > REVH_SYS_CLK_MAX_HZ
#error "rev H: the start-up clock must be 150 MHz or less (docs/13 ファミコンの電源だけで動かすための決まり 1)"
#endif
#if XOSC_HZ != 12000000
#error "rev H: every chip has a 12 MHz crystal"
#endif
#if PICO_RP2350A
#error "rev H: the chips are RP2350B (QFN-80); build with PICO_BOARD famicart_revh"
#endif

static inline void vreg_wait_idle(void) {
    while (powman_hw->vreg & POWMAN_VREG_UPDATE_IN_PROGRESS_BITS)        /* writes are ignored while this is set */
        tight_loop_contents();
}

void revh_vreg_hiz(void) {
    if (revh_vreg_is_hiz())
        return;
    hw_set_bits(&powman_hw->vreg_ctrl, POWMAN_PASSWORD_BITS | POWMAN_VREG_CTRL_UNLOCK_BITS);
    vreg_wait_idle();
    hw_set_bits(&powman_hw->vreg, POWMAN_PASSWORD_BITS | POWMAN_VREG_HIZ_BITS);
    vreg_wait_idle();
}

bool revh_vreg_is_hiz(void) {
    return (powman_hw->vreg & POWMAN_VREG_HIZ_BITS) != 0;
}

uint32_t revh_vreg_raw(void) {
    return powman_hw->vreg;
}

/* "Right after start": before the clock set-up (PICO_RUNTIME_INIT_CLOCKS is 00500), so the regulator is off within
 * the first few hundred microseconds after the boot ROM hands over, whatever main() does first. */
static void revh_runtime_init_vreg(void) {
    revh_vreg_hiz();
}
PICO_RUNTIME_INIT_FUNC_HW(revh_runtime_init_vreg, "00010");

#ifndef FC_REVH_CHIP
#error "FC_REVH_CHIP comes from CMakeLists.txt (FC_BOARD=revh)"
#endif
#if FC_REVH_CHIP == 8 || FC_REVH_CHIP == 9
/* U8 / U9 never raise their own clock (docs/13 rule 9, U8・U9 standby rules 1 / 2): this replaces the SDK's weak
 * runtime_init_clocks() (pico-sdk 2.3.1 runtime_init_clocks.c), which would start both PLLs and run clk_sys at
 * SYS_CLK_HZ before main(). The same steps up to clk_ref = crystal; then clk_sys and clk_peri run from clk_ref at
 * 12 MHz, clk_usb / clk_adc / clk_hstx run from the crystal until main() stops them, and neither PLL is started
 * (main() powers both down in revh_clock_standby(), also after a core-only reset that left them running). The tick
 * generators get 12 cycles = 1 us from clk_ref, as in the SDK. */
void runtime_init_clocks(void) {
    clocks_hw->resus.ctrl = 0;
    xosc_init();
    hw_clear_bits(&clocks_hw->clk[clk_sys].ctrl, CLOCKS_CLK_SYS_CTRL_SRC_BITS);       /* clk_sys from clk_ref */
    while (clocks_hw->clk[clk_sys].selected != 0x1)
        tight_loop_contents();
    hw_clear_bits(&clocks_hw->clk[clk_ref].ctrl, CLOCKS_CLK_REF_CTRL_SRC_BITS);       /* clk_ref from the ROSC */
    while (clocks_hw->clk[clk_ref].selected != 0x1)
        tight_loop_contents();
    clock_configure_undivided(clk_ref, CLOCKS_CLK_REF_CTRL_SRC_VALUE_XOSC_CLKSRC, 0, XOSC_HZ);
    clock_configure_undivided(clk_sys, CLOCKS_CLK_SYS_CTRL_SRC_VALUE_CLK_REF, 0, XOSC_HZ);
    clock_configure_undivided(clk_peri, 0, CLOCKS_CLK_PERI_CTRL_AUXSRC_VALUE_CLK_SYS, XOSC_HZ);
    /* the SDK's runtime_init_post_clock_resets (00600) takes every block out of reset and waits for RESET_DONE "with
     * the peripheral clocks running": USB, ADC and HSTX get the crystal here (12 MHz, no PLL) and revh_clock_standby()
     * stops them in main() */
    clock_configure_undivided(clk_usb, 0, CLOCKS_CLK_USB_CTRL_AUXSRC_VALUE_XOSC_CLKSRC, XOSC_HZ);
    clock_configure_undivided(clk_adc, 0, CLOCKS_CLK_ADC_CTRL_AUXSRC_VALUE_XOSC_CLKSRC, XOSC_HZ);
    clock_configure_undivided(clk_hstx, 0, CLOCKS_CLK_HSTX_CTRL_AUXSRC_VALUE_CLK_SYS, XOSC_HZ);
    for (int i = 0; i < (int)TICK_COUNT; i++)
        tick_start((tick_gen_num_t)i, XOSC_HZ / MHZ);
}
#endif

void revh_start(void) {
    revh_vreg_hiz();
    if (clock_get_hz(clk_sys) > REVH_SYS_CLK_MAX_HZ)                    /* only lowers: never raises the clock */
        set_sys_clock_hz(REVH_SYS_CLK_MAX_HZ, true);
}

void revh_pin_float(unsigned gpio) {
    io_bank0_hw->io[gpio].ctrl = (uint32_t)GPIO_FUNC_NULL << IO_BANK0_GPIO0_CTRL_FUNCSEL_LSB;   /* the reset value */
    hw_write_masked(&pads_bank0_hw->io[gpio], PADS_BANK0_GPIO0_IE_BITS | PADS_BANK0_GPIO0_OD_BITS,
                    PADS_BANK0_GPIO0_IE_BITS | PADS_BANK0_GPIO0_OD_BITS | PADS_BANK0_GPIO0_PUE_BITS | PADS_BANK0_GPIO0_PDE_BITS);
    hw_clear_bits(&pads_bank0_hw->io[gpio], PADS_BANK0_GPIO0_ISO_BITS);
}

void revh_pins_float(uint64_t mask) {
    for (unsigned g = 0; g < NUM_BANK0_GPIOS; g++)
        if (mask & (1ull << g))
            revh_pin_float(g);
}

void revh_clock_standby(void) {
    hard_assert(clock_get_hz(clk_ref) == XOSC_HZ);                         /* runtime_init_clocks: clk_ref = crystal */
    clock_configure_undivided(clk_sys, CLOCKS_CLK_SYS_CTRL_SRC_VALUE_CLK_REF, 0, XOSC_HZ);   /* glitchless switch */
    clock_configure_undivided(clk_peri, 0, CLOCKS_CLK_PERI_CTRL_AUXSRC_VALUE_CLK_SYS, XOSC_HZ);
    clock_stop(clk_usb);
    clock_stop(clk_adc);
    clock_stop(clk_hstx);
    pll_deinit(pll_sys);
    pll_deinit(pll_usb);
}
