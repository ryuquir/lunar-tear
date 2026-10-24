/* Router only; synthesis cores arrive in phase 2. Registers are latched so the
 * synth can be attached without changing the mapper side. */
#include "expaudio.h"
#include "../cart.h"
#include "../profile.h"
#include <string.h>
#ifdef PICO_BUILD
#include "../../pico/board.h"
#include "../../pico/audio_link.h"
#else
#define FC_AUDIO_REMOTE 0
#endif

static expaudio_slot_t g_slots[PROFILE_MAX_AUDIO];
static unsigned g_nslots;
/* Latched register files, enough for every supported chip. */
uint8_t expaudio_regs_vrc6[16];
uint8_t expaudio_regs_vrc7[64]; static uint8_t vrc7_addr;
uint8_t expaudio_regs_mmc5[24];
uint8_t expaudio_regs_n163[128]; static uint8_t n163_addr, n163_inc;
uint8_t expaudio_regs_s5b[16]; static uint8_t s5b_addr;
uint8_t expaudio_regs_fds[16]; uint8_t expaudio_fds_wave[64], expaudio_fds_mod[32]; static uint8_t fds_mod_pos;
static uint8_t g_mask; static uint8_t g_vol[8] = {128,128,128,128,128,128,128,128};
uint8_t expaudio_chip_mask(void) { return g_mask; }
int expaudio_chip_volume(uint8_t chip) { return g_vol[chip & 7]; }

void expaudio_reset(struct cart *c) { (void)c; memset(expaudio_regs_vrc7, 0, sizeof expaudio_regs_vrc7); memset(expaudio_regs_mmc5, 0, sizeof expaudio_regs_mmc5); memset(expaudio_regs_vrc6, 0, sizeof expaudio_regs_vrc6); memset(expaudio_regs_s5b, 0, sizeof expaudio_regs_s5b); memset(expaudio_regs_fds, 0, sizeof expaudio_regs_fds); if (!c) g_mask = 0x7E; /* coprocessor: all chips enabled, the main MCU decides what it sends */ }
void expaudio_configure(struct cart *c, const expaudio_slot_t *slots, unsigned n) {
    g_nslots = n > PROFILE_MAX_AUDIO ? PROFILE_MAX_AUDIO : n;
    memcpy(g_slots, slots, g_nslots * sizeof *slots);
    c->audio_mask = 0;
    for (unsigned i = 0; i < g_nslots; i++) if (g_slots[i].chip) { c->audio_mask |= (uint8_t)(1u << g_slots[i].chip); g_vol[g_slots[i].chip & 7] = g_slots[i].volume ? g_slots[i].volume : 128; }
    g_mask = c->audio_mask;
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
static bool hit_mmc5(uint16_t a, uint8_t v) { if (a >= 0x5000 && a <= 0x5015) { expaudio_regs_mmc5[a - 0x5000] = v; if (a == 0x5003 || a == 0x5007) expaudio_regs_mmc5[a - 0x5000] |= 0x80; /* key marker for the synth */ return true; } return false; }
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
static bool hit_fds(uint16_t a, uint8_t v) {
    if (a >= 0x4040 && a <= 0x407F) { if (expaudio_regs_fds[9] & 0x80) expaudio_fds_wave[a - 0x4040] = v & 0x3F; return true; }
    if (a == 0x4088) { if (expaudio_regs_fds[7] & 0x80) { expaudio_fds_mod[fds_mod_pos] = v & 7; expaudio_fds_mod[(fds_mod_pos + 1) & 31] = v & 7; fds_mod_pos = (fds_mod_pos + 2) & 31; } return true; }
    if (a >= 0x4080 && a <= 0x408F) { expaudio_regs_fds[a - 0x4080] = v; if (a == 0x4085) fds_mod_pos = 0; return true; }
    return false;
}

static bool chip_hit(uint8_t chip, uint16_t a, uint8_t v) {
    switch (chip) {
    case AUDIO_VRC6: return hit_vrc6(a, v);
    case AUDIO_VRC7: return hit_vrc7(a, v);
    case AUDIO_MMC5: return hit_mmc5(a, v);
    case AUDIO_N163: return hit_n163(a, v);
    case AUDIO_S5B:  return hit_s5b(a, v);
    case AUDIO_FDS:  return hit_fds(a, v);
    default: return false;
    }
}
void expaudio_regs_n163_set(uint8_t addr, uint8_t v) { expaudio_regs_n163[addr & 0x7F] = v; }
void expaudio_apply(uint8_t chip, uint16_t native_addr, uint8_t v) { (void)chip_hit(chip, native_addr, v); }

bool expaudio_cpu_write(struct cart *c, uint16_t addr, uint8_t v) {
    (void)c;
    for (unsigned i = 0; i < g_nslots; i++) {
        const expaudio_slot_t *s = &g_slots[i];
        uint16_t a = addr;
        if (s->base) { /* relocated window: map [base, base+window) back to native */
            static const uint16_t native[AUDIO_CHIP_COUNT] = { 0, 0x9000, 0x9010, 0x5000, 0x4800, 0xC000, 0x4040 };
            static const uint16_t width [AUDIO_CHIP_COUNT] = { 0, 0x3004, 0x0021, 0x0016, 0x0001, 0x2001, 0x0050 };
            if (addr < s->base || addr >= s->base + width[s->chip]) continue;
            a = (uint16_t)(native[s->chip] + (addr - s->base));
        }
        bool hit = chip_hit(s->chip, a, v);
#if FC_AUDIO_REMOTE
        if (hit || s->chip == AUDIO_N163) audio_link_send(s->chip, a, v);
#endif
        if (hit && s->exclusive) return true;
    }
    return false;
}
bool expaudio_cpu_read(struct cart *c, uint16_t addr, uint8_t *out) {
    (void)c;
    if ((c->audio_mask & (1u << AUDIO_MMC5)) && addr == 0x5015) { *out = (uint8_t)((expaudio_regs_mmc5[0x15] & 3)); return true; }
    return false;
}

