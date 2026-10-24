/* famicart rev C audio coprocessor (Seeed XIAO RP2040).
 * Receives expansion-audio register writes over UART0 and renders VRC6/VRC7/MMC5/N163/5B/FDS to PWM.
 * The RGB LED shows link state: blue = idle, green = frames flowing, red = framing errors. */
#include "pico/stdlib.h"
#include "hardware/clocks.h"
#include "board.h"
#include "audio_link.h"
#include "../core/audio/expaudio.h"
#include <stdio.h>

void audio_out_init(void); void audio_out_pump(void); uint32_t audio_sample_rate(void);

static void led(bool r, bool g, bool b) { gpio_put(PIN_LED_R, !r); gpio_put(PIN_LED_G, !g); gpio_put(PIN_LED_B, !b); }

int main(void) {
    set_sys_clock_khz(FC_SYS_CLOCK_KHZ, true);
    stdio_init_all();
    for (int p = 0; p < 3; p++) { int pin = (int[]){PIN_LED_R, PIN_LED_G, PIN_LED_B}[p]; gpio_init(pin); gpio_set_dir(pin, true); }
    led(false, false, true);
    audio_link_init();
    audio_out_init();
    expaudio_set_rate(audio_sample_rate());
    expaudio_reset(NULL);
    uint32_t frames = 0; absolute_time_t t_led = make_timeout_time_ms(200), t_rep = make_timeout_time_ms(5000);
    for (;;) {
        uint8_t chip, v; uint16_t addr;
        while (audio_link_poll(&chip, &addr, &v)) {
            frames++;
            if (chip == 0) { if (addr == 0) expaudio_reset(NULL); }
            else expaudio_apply(chip, addr, v);
        }
        audio_out_pump();
        if (time_reached(t_led)) { t_led = make_timeout_time_ms(200); static uint32_t last; led(false, frames != last, frames == last); last = frames; }
        if (time_reached(t_rep)) { t_rep = make_timeout_time_ms(5000); printf("[famicart-audio] frames=%lu rate=%lu\n", (unsigned long)frames, (unsigned long)audio_sample_rate()); }
    }
}
