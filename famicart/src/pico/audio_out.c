/* Expansion audio output: PWM carrier at sysclk/1024 (~246 kHz), 10-bit samples, fed by DMA
 * from a ring buffer that the main loop refills from expaudio_render(). The analogue side is
 * a 2-pole RC low-pass into the cartridge audio mix (pin 46) -- see docs/04_hardware.md. */
#include "board.h"
#include "../core/audio/expaudio.h"
#include "pico/stdlib.h"
#include "hardware/pwm.h"
#include "hardware/dma.h"
#include "hardware/clocks.h"
#include <string.h>
#if PIN_AUDIO_PWM >= 0

#define AUDIO_RING 1024
#define AUDIO_PWM_TOP 1023
static uint16_t ring[AUDIO_RING] __attribute__((aligned(AUDIO_RING * 2)));
static int dma_ch; static uint slice;
static volatile unsigned write_pos;
static int16_t tmp[256];

#define AUDIO_HOLD 4
uint32_t audio_sample_rate(void) { return clock_get_hz(clk_sys) / (AUDIO_PWM_TOP + 1) / AUDIO_HOLD; }

void audio_out_init(void) {
    gpio_set_function(PIN_AUDIO_PWM, GPIO_FUNC_PWM);
    slice = pwm_gpio_to_slice_num(PIN_AUDIO_PWM);
    pwm_config cfg = pwm_get_default_config();
    pwm_config_set_wrap(&cfg, AUDIO_PWM_TOP);
    pwm_init(slice, &cfg, true);
    for (unsigned i = 0; i < AUDIO_RING; i++) ring[i] = (AUDIO_PWM_TOP + 1) / 2;
    dma_ch = dma_claim_unused_channel(true);
    dma_channel_config dc = dma_channel_get_default_config(dma_ch);
    channel_config_set_transfer_data_size(&dc, DMA_SIZE_16);
    channel_config_set_read_increment(&dc, true);
    channel_config_set_write_increment(&dc, false);
    channel_config_set_ring(&dc, false, 11);                 /* 2^11 bytes = 1024 x 16-bit */
    channel_config_set_dreq(&dc, pwm_get_dreq(slice));
    volatile void *cc = (pwm_gpio_to_channel(PIN_AUDIO_PWM) == PWM_CHAN_A) ? (volatile void *)&pwm_hw->slice[slice].cc : (volatile void *)((uint8_t *)&pwm_hw->slice[slice].cc + 2);
    dma_channel_configure(dma_ch, &dc, cc, ring, 0xFFFFFFFF, true);
    write_pos = AUDIO_RING / 2;
}

/* Call frequently from the main loop. Renders only into the half of the ring the DMA is not reading. */
void audio_out_pump(void) {
    unsigned read_pos = (unsigned)(((uintptr_t)dma_hw->ch[dma_ch].read_addr - (uintptr_t)ring) / 2) % AUDIO_RING;
    unsigned free = (read_pos + AUDIO_RING - write_pos - 1) % AUDIO_RING;
    while (free >= 64) {
        unsigned n = free > 256 ? 256 : free;
        unsigned to_end = AUDIO_RING - write_pos; if (n > to_end) n = to_end;
        n &= ~(AUDIO_HOLD - 1); if (!n) break;
        expaudio_render(tmp, n / AUDIO_HOLD);
        for (unsigned i = 0; i < n; i++) ring[write_pos + i] = (uint16_t)(((int32_t)tmp[i / AUDIO_HOLD] + 32768) >> 6);
        write_pos = (write_pos + n) % AUDIO_RING; free -= n;
    }
}
#else
uint32_t audio_sample_rate(void) { return 0; }
void audio_out_init(void) {}
void audio_out_pump(void) {}
#endif
