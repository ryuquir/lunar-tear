#include "profile.h"
#include "rom.h"
#include <string.h>

void profile_default(cart_profile_t *p) {
    memset(p, 0, sizeof *p);
    p->magic = PROFILE_MAGIC; p->version = PROFILE_VERSION;
    p->mapper = 0xFFFF; p->submapper = 0xFF; p->mirroring = 0xFF; p->wram_kb = 0xFF; p->chr_ram_kb = 0xFF;
    for (int i = 0; i < PROFILE_MAX_AUDIO; i++) p->audio_volume[i] = 128;
    p->crc = fc_crc32(0, (const uint8_t *)p, offsetof(cart_profile_t, crc));
}
bool profile_validate(const cart_profile_t *p) {
    if (!p || p->magic != PROFILE_MAGIC || p->version != PROFILE_VERSION) return false;
    return p->crc == fc_crc32(0, (const uint8_t *)p, offsetof(cart_profile_t, crc));
}
