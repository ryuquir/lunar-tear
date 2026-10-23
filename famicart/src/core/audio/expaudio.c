/* Router only; synthesis cores arrive in phase 2. Registers are latched so the
 * synth can be attached without changing the mapper side. */
#include "expaudio.h"
#include "../cart.h"
#include "../profile.h"
#include <string.h>

static expaudio_slot_t g_slots[PROFILE_MAX_AUDIO];
static unsigned g_nslots;
/* Latched register files, enough for every supported chip. */
uint8_t expaudio_regs_vrc6[16];
uint8_t expaudio_regs_vrc7[64]; static uint8_t vrc7_addr;
uint8_t expaudio_regs_mmc5[24];
uint8_t expaudio_regs_n163[128]; static uint8_t n163_addr, n163_inc;
uint8_t expaudio_regs_s5b[16]; static uint8_t s5b_addr;
uint8_t expaudio_regs_fds[16];

void expaudio_reset(struct cart *c) { (void)c; memset(expaudio_regs_vrc7, 0, sizeof expaudio_regs_vrc7); memset(expaudio_regs_mmc5, 0, sizeof expaudio_regs_mmc5); }
void expaudio_configure(struct cart *c, const expaudio_slot_t *slots, unsigned n) {
    g_nslots = n > PROFILE_MAX_AUDIO ? PROFILE_MAX_AUDIO : n;
    memcpy(g_slots, slots, g_nslots * sizeof *slots);
    c->audio_mask = 0;
    for (unsigned i = 0; i < g_nslots; i++) if (g_slots[i].chip) c->audio_mask |= (uint8_t)(1u << g_slots[i].chip);
}

/* Native register windows. `rel` = addr - base when relocated. */
static bool hit_vrc6(uint16_t a, uint8_t v) {
    if ((a & 0xF000) == 0x9000 || (a & 0xF000) == 0xA000 || (a & 0xF000) == 0xB000) {
        unsigned r = ((a >> 12) - 9) * 4 + (a & 3); if (r < 12 || (a & 0xF003) == 0xB003) { expaudio_regs_vrc6[r & 15] = v; return r != 11; }
    }
    return false;
}
static bool hit_vrc7(uint16_t a, uint8_t v) {
    if ((a & 0xF030) == 0x9010) { vrc7_addr = v & 0x3F; return true; }
    if ((a & 0xF030) == 0x9030) { expaudio_regs_vrc7[vrc7_addr] = v; return true; }
    return false;
}
static bool hit_mmc5(uint16_t a, uint8_t v) { if (a >= 0x5000 && a <= 0x5015) { expaudio_regs_mmc5[a - 0x5000] = v; return true; } return false; }
static bool hit_n163(uint16_t a, uint8_t v) {
    if ((a & 0xF800) == 0x4800) { expaudio_regs_n163[n163_addr & 0x7F] = v; if (n163_inc) n163_addr = (n163_addr + 1) & 0x7F; return false; /* mapper RAM too */ }
    if ((a & 0xF800) == 0xF800) { n163_addr = v & 0x7F; n163_inc = v >> 7; return false; }
    return false;
}
static bool hit_s5b(uint16_t a, uint8_t v) {
    if ((a & 0xE000) == 0xC000) { s5b_addr = v & 0x0F; return true; }
    if ((a & 0xE000) == 0xE000) { expaudio_regs_s5b[s5b_addr] = v; return true; }
    return false;
}
static bool hit_fds(uint16_t a, uint8_t v) { if (a >= 0x4080 && a <= 0x408F) { expaudio_regs_fds[a - 0x4080] = v; return true; } return false; }

bool expaudio_cpu_write(struct cart *c, uint16_t addr, uint8_t v) {
    (void)c;
    for (unsigned i = 0; i < g_nslots; i++) {
        const expaudio_slot_t *s = &g_slots[i];
        uint16_t a = addr;
        if (s->base) { /* relocated window: map [base, base+window) back to native */
            static const uint16_t native[AUDIO_CHIP_COUNT] = { 0, 0x9000, 0x9010, 0x5000, 0x4800, 0xC000, 0x4080 };
            static const uint16_t width [AUDIO_CHIP_COUNT] = { 0, 0x3004, 0x0021, 0x0016, 0x0001, 0x2001, 0x0010 };
            if (addr < s->base || addr >= s->base + width[s->chip]) continue;
            a = (uint16_t)(native[s->chip] + (addr - s->base));
        }
        bool hit = false;
        switch (s->chip) {
        case AUDIO_VRC6: hit = hit_vrc6(a, v); break;
        case AUDIO_VRC7: hit = hit_vrc7(a, v); break;
        case AUDIO_MMC5: hit = hit_mmc5(a, v); break;
        case AUDIO_N163: hit = hit_n163(a, v); break;
        case AUDIO_S5B:  hit = hit_s5b(a, v); break;
        case AUDIO_FDS:  hit = hit_fds(a, v); break;
        default: break;
        }
        if (hit && s->exclusive) return true;
    }
    return false;
}
bool expaudio_cpu_read(struct cart *c, uint16_t addr, uint8_t *out) {
    (void)c;
    if ((c->audio_mask & (1u << AUDIO_MMC5)) && addr == 0x5015) { *out = (uint8_t)((expaudio_regs_mmc5[0x15] & 3)); return true; }
    return false;
}
void expaudio_render(int16_t *buf, unsigned n) { memset(buf, 0, n * sizeof *buf); }
