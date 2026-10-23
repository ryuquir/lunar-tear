/* Sunsoft-3 (67), Sunsoft-4 (68), FME-7 / Sunsoft 5A/5B (69). */
#include "../mapper.h"

static void s3_init(cart_t *c) { generic_state_t *g = &c->s.g; cart_set_prg16k(c, 0, 0); cart_set_prg16k(c, 1, -1); for (unsigned i = 0; i < 4; i++) cart_set_chr2k(c, i, (int32_t)i); g->b[0] = false; g->b[1] = false; g->r16[0] = 0; }
static void s3_write(cart_t *c, uint16_t a, uint8_t v) {
    generic_state_t *g = &c->s.g; if (a < 0x8000) return;
    switch (a & 0xF800) {
    case 0x8800: cart_set_chr2k(c, 0, v); break; case 0x9800: cart_set_chr2k(c, 1, v); break;
    case 0xA800: cart_set_chr2k(c, 2, v); break; case 0xB800: cart_set_chr2k(c, 3, v); break;
    case 0xC800: if (!g->b[1]) g->r16[0] = (uint16_t)((g->r16[0] & 0x00FF) | (v << 8)); else g->r16[0] = (uint16_t)((g->r16[0] & 0xFF00) | v); g->b[1] = !g->b[1]; break;
    case 0xD800: g->b[0] = (v & 0x10); g->b[1] = false; cart_irq(c, false); break;
    case 0xE800: { static const mirroring_t mm[4] = { MIRROR_V, MIRROR_H, MIRROR_1A, MIRROR_1B }; cart_set_mirroring(c, mm[v & 3]); } break;
    case 0xF800: cart_set_prg16k(c, 0, v); break;
    }
}
static void s3_cycle(cart_t *c) { generic_state_t *g = &c->s.g; if (!g->b[0]) return; if (g->r16[0] == 0) { g->b[0] = false; cart_irq(c, true); g->r16[0] = 0xFFFF; } else g->r16[0]--; }
const mapper_desc_t mapper_067 = { 67, "Sunsoft-3", MF_CPU_CYCLE, s3_init, s3_write, NULL, NULL, s3_cycle };

static void s4_sync(cart_t *c) {
    generic_state_t *g = &c->s.g;
    for (unsigned i = 0; i < 4; i++) cart_set_chr2k(c, i, g->regs[i]);
    if (g->regs[6] & 0x10) {
        bool h = g->regs[6] & 1;
        cart_set_nt_chr1k(c, 0, 0x80 | g->regs[4]); cart_set_nt_chr1k(c, 1, 0x80 | (h ? g->regs[4] : g->regs[5]));
        cart_set_nt_chr1k(c, 2, 0x80 | (h ? g->regs[5] : g->regs[4])); cart_set_nt_chr1k(c, 3, 0x80 | g->regs[5]);
    } else cart_set_mirroring(c, (g->regs[6] & 1) ? MIRROR_H : MIRROR_V);
    cart_set_prg16k(c, 0, g->regs[7] & 0x0F); cart_set_prg16k(c, 1, -1);
    if (c->wram_size && (g->regs[7] & 0x10)) cart_set_wram_6000(c, 0, true); else cart_unmap_6000(c);
}
static void s4_init(cart_t *c) { generic_state_t *g = &c->s.g; for (int i = 0; i < 4; i++) g->regs[i] = (uint8_t)i; g->regs[4] = g->regs[5] = 0; g->regs[6] = 0; g->regs[7] = 0x10; s4_sync(c); }
static void s4_write(cart_t *c, uint16_t a, uint8_t v) { generic_state_t *g = &c->s.g; if (a < 0x8000) return; g->regs[(a >> 12) - 8] = v; s4_sync(c); }
const mapper_desc_t mapper_068 = { 68, "Sunsoft-4", 0, s4_init, s4_write, NULL, NULL, NULL };

static void fme7_sync(cart_t *c) {
    fme7_state_t *s = &c->s.fme7;
    for (unsigned i = 0; i < 8; i++) cart_set_chr1k(c, i, s->chr[i]);
    if (s->wram_bank & 0x40) { if (s->wram_bank & 0x80) cart_set_wram_6000(c, s->wram_bank & 0x3F, true); else cart_unmap_6000(c); }
    else cart_set_prg8k_6000(c, s->wram_bank & 0x3F);
    for (unsigned i = 0; i < 3; i++) cart_set_prg8k(c, i, s->prg[i] & 0x3F);
    cart_set_prg8k(c, 3, -1);
    static const mirroring_t mm[4] = { MIRROR_V, MIRROR_H, MIRROR_1A, MIRROR_1B };
    cart_set_mirroring(c, mm[s->wram_en & 3]);
}
static void fme7_init(cart_t *c) { fme7_state_t *s = &c->s.fme7; s->cmd = 0; for (int i = 0; i < 8; i++) s->chr[i] = (uint8_t)i; s->prg[0] = 0; s->prg[1] = 1; s->prg[2] = 2; s->wram_bank = 0; s->wram_en = 0; s->irq_enable = 0; s->irq_counter = 0; fme7_sync(c); }
static void fme7_write(cart_t *c, uint16_t a, uint8_t v) {
    fme7_state_t *s = &c->s.fme7; if (a < 0x8000) return;
    switch (a & 0xE000) {
    case 0x8000: s->cmd = v & 0x0F; return;
    case 0xA000:
        if (s->cmd < 8) s->chr[s->cmd] = v;
        else if (s->cmd == 8) s->wram_bank = v;
        else if (s->cmd <= 0xB) s->prg[s->cmd - 9] = v;
        else if (s->cmd == 0xC) s->wram_en = v & 3;
        else if (s->cmd == 0xD) { s->irq_enable = v; cart_irq(c, false); return; }
        else if (s->cmd == 0xE) { s->irq_counter = (uint16_t)((s->irq_counter & 0xFF00) | v); return; }
        else { s->irq_counter = (uint16_t)((s->irq_counter & 0x00FF) | (v << 8)); return; }
        break;
    default: return; /* $C000/$E000: 5B audio via router */
    }
    fme7_sync(c);
}
static void fme7_cycle(cart_t *c) { fme7_state_t *s = &c->s.fme7; if (!(s->irq_enable & 0x80)) return; if (s->irq_counter == 0 && (s->irq_enable & 1)) cart_irq(c, true); s->irq_counter--; }
const mapper_desc_t mapper_069 = { 69, "Sunsoft-FME-7/5B", MF_CPU_CYCLE, fme7_init, fme7_write, NULL, NULL, fme7_cycle };
