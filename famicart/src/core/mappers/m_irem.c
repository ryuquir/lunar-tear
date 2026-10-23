/* Irem G-101 (32) and H3001 (65). */
#include "../mapper.h"
static void g101_sync(cart_t *c) {
    generic_state_t *g = &c->s.g;
    if (g->regs[2] & 2) { cart_set_prg8k(c, 0, -2); cart_set_prg8k(c, 2, g->regs[0]); } else { cart_set_prg8k(c, 0, g->regs[0]); cart_set_prg8k(c, 2, -2); }
    cart_set_prg8k(c, 1, g->regs[1]); cart_set_prg8k(c, 3, -1);
    for (unsigned i = 0; i < 8; i++) cart_set_chr1k(c, i, g->regs[8 + i]);
    if (c->submapper == 1) cart_set_mirroring(c, MIRROR_1A); else cart_set_mirroring(c, (g->regs[2] & 1) ? MIRROR_H : MIRROR_V);
    if (c->wram_size) cart_set_wram_6000(c, 0, true);
}
static void g101_init(cart_t *c) { generic_state_t *g = &c->s.g; g->regs[0] = 0; g->regs[1] = 1; g->regs[2] = 0; for (int i = 0; i < 8; i++) g->regs[8 + i] = (uint8_t)i; g101_sync(c); }
static void g101_write(cart_t *c, uint16_t a, uint8_t v) {
    generic_state_t *g = &c->s.g; if (a < 0x8000) return;
    switch (a & 0xF000) { case 0x8000: g->regs[0] = v & 0x1F; break; case 0x9000: g->regs[2] = v & 3; break; case 0xA000: g->regs[1] = v & 0x1F; break; case 0xB000: g->regs[8 + (a & 7)] = v; break; default: return; }
    g101_sync(c);
}
const mapper_desc_t mapper_032 = { 32, "Irem-G101", 0, g101_init, g101_write, NULL, NULL, NULL };

static void h3001_sync(cart_t *c) { generic_state_t *g = &c->s.g; cart_set_prg8k(c, 0, g->regs[0]); cart_set_prg8k(c, 1, g->regs[1]); cart_set_prg8k(c, 2, g->regs[2]); cart_set_prg8k(c, 3, -1);
    for (unsigned i = 0; i < 8; i++) cart_set_chr1k(c, i, g->regs[8 + i]);
    cart_set_mirroring(c, (g->regs[3] & 0x80) ? MIRROR_H : MIRROR_V); }
static void h3001_init(cart_t *c) { generic_state_t *g = &c->s.g; g->regs[0] = 0; g->regs[1] = 1; g->regs[2] = (uint8_t)(c->prg_pages - 2); g->regs[3] = 0; for (int i = 0; i < 8; i++) g->regs[8 + i] = (uint8_t)i; g->b[0] = false; h3001_sync(c); }
static void h3001_write(cart_t *c, uint16_t a, uint8_t v) {
    generic_state_t *g = &c->s.g; if (a < 0x8000) return;
    switch (a) {
    case 0x8000: g->regs[0] = v; break; case 0xA000: g->regs[1] = v; break; case 0xC000: g->regs[2] = v; break;
    case 0x9001: g->regs[3] = v; break;
    case 0x9003: g->b[0] = v & 0x80; cart_irq(c, false); return;
    case 0x9004: g->r16[0] = g->r16[1]; cart_irq(c, false); return;
    case 0x9005: g->r16[1] = (uint16_t)((g->r16[1] & 0x00FF) | (v << 8)); return;
    case 0x9006: g->r16[1] = (uint16_t)((g->r16[1] & 0xFF00) | v); return;
    default: if ((a & 0xF000) == 0xB000) g->regs[8 + (a & 7)] = v; else return;
    }
    h3001_sync(c);
}
static void h3001_cycle(cart_t *c) { generic_state_t *g = &c->s.g; if (g->b[0] && g->r16[0]) { if (--g->r16[0] == 0) cart_irq(c, true); } }
const mapper_desc_t mapper_065 = { 65, "Irem-H3001", MF_CPU_CYCLE, h3001_init, h3001_write, NULL, NULL, h3001_cycle };
