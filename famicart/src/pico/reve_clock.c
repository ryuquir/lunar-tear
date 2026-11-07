/* rev E: clock bring-up shared by U1/U2/U3. The flash (QSPI/XIP) divider is raised before sys_clk goes to
 * 240 MHz so the flash runs at 80 MHz (it still serves big games' pages straight from XIP). */
#include "pico/stdlib.h"
#include "hardware/vreg.h"
#include "hardware/clocks.h"
#include "hardware/sync.h"
#include "hardware/structs/qmi.h"
#include "board.h"

static void __not_in_flash_func(set_flash_div)(uint32_t div) {
    uint32_t ints = save_and_disable_interrupts();
    qmi_hw->m[0].timing = (qmi_hw->m[0].timing & ~QMI_M0_TIMING_CLKDIV_BITS) | (div << QMI_M0_TIMING_CLKDIV_LSB);
    __dsb(); __isb();
    restore_interrupts(ints);
}
void reve_clock_init(void) {
    vreg_set_voltage(VREG_VOLTAGE_1_15);
    busy_wait_us(2000);
    set_flash_div(3);
    set_sys_clock_khz(FC_SYS_CLOCK_KHZ, true);
}
