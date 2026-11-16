/* famicart rev H: idle program, one build per chip (FC_BOARD=revh, FC_REVH_CHIP = 1-6, 8, 9; docs/13_rev_h_plan.md
 * "ファームの土台"). No mapper: it shows that the chip runs, keeps everything that reaches the console quiet, and on the
 * hub reports the supplies over USB.
 *
 * Every chip:
 *   - revh_start(): on-chip regulator to high impedance, clk_sys at most 150 MHz.
 *   - pins on nets that reach the console's card edge (REVH_CONSOLE_MASK: CPU / PPU bus, raw strobes, RSEL_D / WS_D /
 *     PWS_D, /IRQ gate, CIRAM /CE / A10, audio PWM, the hub's M2 branch) become inputs without pulls (rev G rule "ピン
 *     のプルを切る"); nothing drives them. With U3's pull-down gone, CIRAM /CE stays high through its 10k (the console's
 *     VRAM is not selected) and /IRQ stays released through Q5's 2.2k gate pull-down.
 *   - LED<n>: one short flash a second while VSEL_S is low, two while it is high. VSEL_S is read as an input without pulls.
 *   - every other GPIO (LINK, PLINK, WLINK, XLINK, XSTAT, PEV, HIRQ, IRQ4 / 5, spare pins) keeps its reset state.
 * U1-U5: the SDK's clock set-up runs them at 150 MHz until main(), then clk_sys drops to the 12 MHz crystal with both
 * PLLs off (docs/13: standby of unused chips). U8, U9: never above 12 MHz (docs/13 rule 9): revh_start.c replaces
 * the SDK's clock set-up for them, and the PLLs never start.
 * Hub (U6), at 150 MHz:
 *   - SWD master pins of the seven targets: SWCLK driven low, SWDIO pulled up (docs/13 "起動・書き込み・リセット").
 *   - nRST released (SIO input, pad pulls off: the board's 10k holds RUN high); VSEL left low (input, pad pulls off:
 *     the board's 100k holds Q7 off).
 *   - microSD: card detect with the pad pull-up; CMD / DAT0-3 inputs without pad pulls so that the board's pull-ups
 *     hold them high; CLK stays at reset (pad pull-down, low). The card is not initialised.
 *   - ADC on V5S, EXT and VBUS_S. The D+ pull-up is forced off first (a core-only reset can leave it on). USB CDC
 *     stdio starts only once VBUS_S has read 1.5 V or more three times in a row; the D+ pull-up is off again
 *     (tud_disconnect) and the controller's VBUS-detect override reads "absent" while VBUS_S is below 1.4 V.
 *     VBUS_S is an ADC pin, not the USB block's VBUS_DETECT input, so the override (USB_PWR) stands in for it. The
 *     datasheet does not say that the override gates the pull-up, so the pull-up is switched explicitly.
 *   - U7 on QMI CS1: window 1 set to a plain 03h serial read at clk_sys / 6, the first four bytes read through the
 *     uncached, untranslated alias. Read only; FLASH_DEVINFO is left alone (only the boot ROM's erase / program need it).
 *   - once a second over USB: V5S, EXT, VBUS_S in volts (at the pin and before the divider), VSEL_S, SD_CD, nRST,
 *     clk_sys, the regulator state and U7's first bytes.
 *
 * docs/13 rule 1 (U1 drives the idle $4C within 8 ms of power-on) is NOT met: in a powered Famicom the CPU leaves
 * reset (about 17 ms after power-on) and executes garbage. It reads $00 while any of U1 / U3 / U4 still has its
 * reset pull-downs on the data lines (boot ROM, crystal wait, runtime init; for good on a chip with no program),
 * open bus once all three run this program. The cartridge drives no console net (the bus pins float, CIRAM /CE is held high by R25 10k, /IRQ is
 * released by R21 on Q5's gate), so nothing fights the console and no hardware is at risk; only the picture and sound
 * are garbage. Run the U1 idle build on USB power without a console, or in the console with its reset button held
 * (also the clean way to read V5S during bring-up). */
#include "pico/stdlib.h"
#include "pico/binary_info.h"
#include "hardware/gpio.h"
#include "hardware/clocks.h"
#include "revh_start.h"

#ifndef FC_REVH_PINS
#error "FC_REVH_PINS (the chip's pins header) comes from CMakeLists.txt: configure with -DFC_BOARD=revh -DFC_REVH_CHIP=<n>"
#endif
#include FC_REVH_PINS
#if REVH_CHIP != FC_REVH_CHIP
#error "FC_REVH_PINS does not belong to FC_REVH_CHIP"
#endif

#define STR_(x) #x
#define STR(x) STR_(x)
bi_decl(bi_program_description("famicart rev H idle program, U" STR(REVH_CHIP) " (" REVH_ROLE ")"));
bi_decl(bi_1pin_with_name(PIN_LED, "LED"));

#define BIT(g) (1ull << (g))
_Static_assert((REVH_CONSOLE_MASK & (BIT(PIN_LED) | BIT(PIN_VSEL_S))) == 0, "the LED and VSEL_S never reach the console");

/* One flash (100 ms) a second, a second flash 250 ms later while VSEL_S is high. */
static bool led_on(uint32_t ms, bool vsel) {
    uint32_t ph = ms % 1000u;
    return ph < 100u || (vsel && ph >= 250u && ph < 350u);
}

static void own_common_pins(void) {
    gpio_disable_pulls(PIN_VSEL_S);                 /* before gpio_init releases the pad isolation */
    gpio_init(PIN_VSEL_S);                          /* input */
    gpio_init(PIN_LED);
    gpio_set_dir(PIN_LED, GPIO_OUT);                /* gpio_init left the output value at 0: LED off */
}

#if REVH_IS_HUB
#include <stdio.h>
#include "pins_hub.h"
#include "pico/stdio_usb.h"
#include "hardware/adc.h"
#include "hardware/sync.h"
#include "hardware/structs/qmi.h"
#include "hardware/structs/usb.h"
#include "hardware/regs/addressmap.h"
#include "tusb.h"

_Static_assert(HUB_ADC_BASE_PIN == ADC_BASE_PIN, "ADC0 is GPIO40 on the RP2350B (PICO_RP2350A 0)");
_Static_assert(HUB_XIP_CS1_FUNC == GPIO_FUNC_XIP_CS1, "QMI CS1n is function 9 on GPIO47");
_Static_assert(HUB_HM2_FUNC == GPIO_FUNC_PWM && HUB_PWM2_FUNC == GPIO_FUNC_PWM, "PWM is function 4");
_Static_assert(HUB_SD_SPI_SCK_FUNC == GPIO_FUNC_SPI && HUB_SD_SPI_TX_FUNC == GPIO_FUNC_SPI && HUB_SD_SPI_RX_FUNC == GPIO_FUNC_SPI,
               "SPI is function 1");
/* every pin hub_main() sets up, the SWCLK outputs included */
#define HUB_OWNED (HUB_SWD_SWCLK_MASK | HUB_SWD_SWDIO_MASK | BIT(HUB_NRST_PIN) | BIT(HUB_VSEL_PIN) | BIT(HUB_LED_PIN) | \
                   BIT(HUB_SD_CD_PIN) | BIT(PIN_SD_CMD) | BIT(PIN_SD_DAT0) | BIT(PIN_SD_DAT1) | BIT(PIN_SD_DAT2) | \
                   BIT(PIN_SD_DAT3) | BIT(HUB_ADC_V5S_PIN) | BIT(HUB_ADC_EXT_PIN) | BIT(HUB_ADC_VBUS_S_PIN) | \
                   BIT(HUB_XIP_CS1_PIN))
_Static_assert((REVH_CONSOLE_MASK & HUB_OWNED) == 0, "the hub's own pins never reach the console");

static const uint8_t swclk_pins[HUB_SWD_COUNT] = HUB_SWD_SWCLK_PINS;
static const uint8_t swdio_pins[HUB_SWD_COUNT] = HUB_SWD_SWDIO_PINS;

static void hub_pins(void) {
    for (unsigned i = 0; i < HUB_SWD_COUNT; i++) {
        gpio_init(swclk_pins[i]);
        gpio_set_dir(swclk_pins[i], GPIO_OUT);      /* SWCLK low */
        gpio_set_pulls(swdio_pins[i], true, false);
        gpio_init(swdio_pins[i]);                   /* SWDIO input, pulled up */
    }
    gpio_disable_pulls(HUB_NRST_PIN);
    gpio_init(HUB_NRST_PIN);                        /* released; output value 0 kept for the open-drain use later */
    gpio_disable_pulls(HUB_VSEL_PIN);
    gpio_init(HUB_VSEL_PIN);                        /* low through the board's 100k: +1V1 at 1.092 V */
    gpio_set_pulls(HUB_SD_CD_PIN, true, false);
    gpio_init(HUB_SD_CD_PIN);
    static const uint8_t sd_up[] = { PIN_SD_CMD, PIN_SD_DAT0, PIN_SD_DAT1, PIN_SD_DAT2, PIN_SD_DAT3 };
    for (unsigned i = 0; i < sizeof sd_up; i++) {
        gpio_disable_pulls(sd_up[i]);
        gpio_init(sd_up[i]);
    }
    adc_init();
    adc_gpio_init(HUB_ADC_V5S_PIN);
    adc_gpio_init(HUB_ADC_EXT_PIN);
    adc_gpio_init(HUB_ADC_VBUS_S_PIN);
}

/* mV at the pin: the mean of 8 conversions, against the nominal ADC_AVDD (+3V3) */
static uint32_t adc_pin_mv(unsigned ch) {
    adc_select_input(ch);
    uint32_t sum = 0;
    for (int i = 0; i < 8; i++)
        sum += adc_read();
    return sum * HUB_ADC_VREF_MV / (8u * 4096u);
}

static uint32_t source_mv(uint32_t pin_mv, uint32_t r_top, uint32_t r_bottom) {
    return r_bottom ? pin_mv * (r_top + r_bottom) / r_bottom : pin_mv;
}

/* QMI window 1 (U7): 03h serial read, SCK = clk_sys / 6 (25 MHz at 150 MHz; the W25Q128JV reads 03h up to 50 MHz). Set
 * from RAM with interrupts off, as the SDK does for window 1, so that no XIP fetch runs while the QMI is reprogrammed. */
static void __no_inline_not_in_flash_func(u7_window_setup)(void) {
    uint32_t ints = save_and_disable_interrupts();
    qmi_hw->m[1].timing = 1u << QMI_M1_TIMING_COOLDOWN_LSB | 6u << QMI_M1_TIMING_CLKDIV_LSB;
    qmi_hw->m[1].rfmt = QMI_M1_RFMT_PREFIX_WIDTH_VALUE_S << QMI_M1_RFMT_PREFIX_WIDTH_LSB |
                        QMI_M1_RFMT_ADDR_WIDTH_VALUE_S << QMI_M1_RFMT_ADDR_WIDTH_LSB |
                        QMI_M1_RFMT_DATA_WIDTH_VALUE_S << QMI_M1_RFMT_DATA_WIDTH_LSB |
                        QMI_M1_RFMT_PREFIX_LEN_VALUE_8 << QMI_M1_RFMT_PREFIX_LEN_LSB;
    qmi_hw->m[1].rcmd = 0x03u << QMI_M1_RCMD_PREFIX_LSB;
    __dsb();
    restore_interrupts(ints);
}

static void u7_setup(void) {
    u7_window_setup();
    gpio_disable_pulls(HUB_XIP_CS1_PIN);            /* 2.2k pull-up on the board; the QMI drives CS1n from here on */
    gpio_set_function(HUB_XIP_CS1_PIN, GPIO_FUNC_XIP_CS1);
}

static void u7_read4(uint8_t out[4]) {
    const volatile uint8_t *u7 = (const volatile uint8_t *)(XIP_NOCACHE_NOALLOC_NOTRANSLATE_BASE + 0x01000000u);
    for (int i = 0; i < 4; i++)
        out[i] = u7[i];
}

static bool usb_started, usb_on;

/* usb_on starts false, so make it true of the hardware: the SDK's start-up does not reset USBCTRL, and after a
 * core-only reset (e.g. a debugger's warm reset through J5) SIE_CTRL.PULLUP_EN can still be set from the previous
 * run, pulling D+ up into a host that has no VBUS (docs/13 rule 8). USBCTRL is out of reset by now (the SDK's
 * post-clock resets). */
static void usb_force_off(void) {
    hw_clear_bits(&usb_hw->sie_ctrl, USB_SIE_CTRL_PULLUP_EN_BITS);
    usb_hw->pwr = USB_USB_PWR_VBUS_DETECT_OVERRIDE_EN_BITS;   /* the controller sees VBUS absent */
}

/* D+ pull-up only while VBUS is present: on after three readings in a row (30 ms) at or above HUB_VBUS_S_ON_MV, off
 * below HUB_VBUS_S_OFF_MV. Any reading below HUB_VBUS_S_ON_MV starts the count again; between the two thresholds the
 * pull-up stays as it is. TinyUSB's dcd_init() forces VBUS-detect on and enables the pull-up, so the stack starts
 * only when VBUS is first seen. */
static void usb_follow_vbus(uint32_t vbus_s_mv) {
    static unsigned above;
    if (vbus_s_mv < HUB_VBUS_S_ON_MV)
        above = 0;
    else if (above < 3)
        above++;
    bool want = above >= 3 ? true : (vbus_s_mv < HUB_VBUS_S_OFF_MV ? false : usb_on);
    if (want == usb_on)
        return;
    if (want) {
        if (!usb_started) {
            stdio_usb_init();                       /* pull-up on; USB_PWR = VBUS_DETECT | override */
            usb_started = true;
        } else {
            usb_hw->pwr = USB_USB_PWR_VBUS_DETECT_BITS | USB_USB_PWR_VBUS_DETECT_OVERRIDE_EN_BITS;
            tud_connect();
        }
    } else {
        tud_disconnect();                           /* SIE_CTRL.PULLUP_EN off */
        usb_hw->pwr = USB_USB_PWR_VBUS_DETECT_OVERRIDE_EN_BITS;   /* the controller sees VBUS absent */
    }
    usb_on = want;
}

static void print_mv(const char *name, uint32_t mv) {
    printf("%s %u.%03u V", name, (unsigned)(mv / 1000u), (unsigned)(mv % 1000u));
}

static void hub_report(void) {
    uint32_t v5s = adc_pin_mv(HUB_ADC_V5S_CH), ext = adc_pin_mv(HUB_ADC_EXT_CH), vbs = adc_pin_mv(HUB_ADC_VBUS_S_CH);
    uint8_t u7[4];
    u7_read4(u7);
    printf("U6 hub  ");
    print_mv("V5S", v5s);
    print_mv(" (+5V", source_mv(v5s, HUB_ADC_V5S_R_TOP, HUB_ADC_V5S_R_BOTTOM));
    print_mv(")  EXT", source_mv(ext, HUB_ADC_EXT_R_TOP, HUB_ADC_EXT_R_BOTTOM));
    print_mv("  VBUS_S", vbs);
    print_mv(" (VBUS", source_mv(vbs, HUB_ADC_VBUS_S_R_TOP, HUB_ADC_VBUS_S_R_BOTTOM));
    printf(")  VSEL_S %d  SD_CD %d  nRST %d  clk_sys %u MHz  VREG %s (0x%04x)  U7 %02x %02x %02x %02x\n",
           gpio_get(HUB_VSEL_PIN), gpio_get(HUB_SD_CD_PIN), gpio_get(HUB_NRST_PIN),
           (unsigned)(clock_get_hz(clk_sys) / 1000000u), revh_vreg_is_hiz() ? "hiz" : "ON",
           (unsigned)(revh_vreg_raw() & 0xffffu), u7[0], u7[1], u7[2], u7[3]);
}

static void __attribute__((noreturn)) hub_main(void) {
    usb_force_off();
    hub_pins();
    u7_setup();
    uint32_t next_report = 1000;
    for (;;) {
        uint32_t now = to_ms_since_boot(get_absolute_time());
        usb_follow_vbus(adc_pin_mv(HUB_ADC_VBUS_S_CH));
        gpio_put(PIN_LED, led_on(now, gpio_get(PIN_VSEL_S)));
        if ((int32_t)(now - next_report) >= 0) {
            next_report += 1000;
            if (usb_on)
                hub_report();
        }
        sleep_ms(10);
    }
}
#endif /* REVH_IS_HUB */

int main(void) {
    revh_start();
    revh_pins_float(REVH_CONSOLE_MASK);
    own_common_pins();
#if REVH_IS_HUB
    hub_main();
#else
    revh_clock_standby();
    for (;;) {
        uint32_t now = to_ms_since_boot(get_absolute_time());
        gpio_put(PIN_LED, led_on(now, gpio_get(PIN_VSEL_S)));
        sleep_ms(50);
    }
#endif
}
