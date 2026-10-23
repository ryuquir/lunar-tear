/* Expansion-audio register router (phase 2 implements the synthesis).
 *
 * Every CPU write passes through expaudio_cpu_write() first. A chip that is enabled
 * in the cartridge profile claims its register window (native address or relocated
 * via profile.base). Returning true means the write was consumed exclusively and
 * must NOT reach the mapper; returning false lets the mapper see it as usual.
 * This is what allows "MMC5 banking + VRC7 sound": VRC7's $9010/$9030 are ROM
 * addresses for MMC5, so the audio chip can take them without conflict. */
#pragma once
#include "../fc_types.h"
struct cart;

typedef struct {
    uint8_t  chip;       /* audio_chip_t */
    uint8_t  exclusive;
    uint16_t base;       /* 0 = native */
    uint8_t  volume;     /* 128 = nominal */
} expaudio_slot_t;

void expaudio_reset(struct cart *c);
void expaudio_configure(struct cart *c, const expaudio_slot_t *slots, unsigned n);
bool expaudio_cpu_write(struct cart *c, uint16_t addr, uint8_t v);
bool expaudio_cpu_read(struct cart *c, uint16_t addr, uint8_t *out);   /* MMC5 $5015, N163 $4800 data, S5B none */
/* Render n mono samples (signed 16-bit) into buf at the configured rate. */
void expaudio_render(int16_t *buf, unsigned n);
