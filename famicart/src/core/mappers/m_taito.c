/* Taito TC0190/TC0350 (33), TC0690 (48), X1-005 (80/207), X1-017 (82). */
#include "../mapper.h"

static void tc_sync(cart_t *c) {
    taito_state_t *s = &c->s.taito;
    cart_set_prg8k(c, 0, s->prg[0]); cart_set_prg8k(c, 1, s->prg[1]); cart_set_prg8k(c, 2, -2); cart_set_prg8k(c, 3, -1);
    cart_set_chr2k(c, 0, s->chr[0]); cart_set_chr2k(c, 1, s->chr[1]);
    for (unsigned i = 0; i < 4; i++) cart_set_chr1k(c, 4 + i, s->chr[2 + i]);
    cart_set_mirroring(c, s->mirroring ? MIRROR_H : MIRROR_V);
}
static void tc_init(cart_t *c) { taito_state_t *s = &c->s.taito; s->prg[0] = 0; s->prg[1] = 1; s->chr[0] = 0; s->chr[1] = 1; for (int i = 0; i < 4; i++) s->chr[2 + i] = (uint8_t)(4 + i); s->mirroring = 0; s->irq_enable = 0; tc_sync(c); }
static void tc_write(cart_t *c, uint16_t a, uint8_t v) {
    taito_state_t *s = &c->s.taito; if (a < 0x8000) return;
    bool m48 = c->mapper_id == 48;
    switch (a & 0xE003) {
    case 0x8000: s->prg[0] = v & 0x3F; if (!m48) s->mirroring = v >> 6; break;
    case 0x8001: s->prg[1] = v & 0x3F; break;
    case 0x8002: s->chr[0] = v; break; case 0x8003: s->chr[1] = v; break;
    case 0xA000: case 0xA001: case 0xA002: case 0xA003: s->chr[2 + (a & 3)] = v; break;
    case 0xC000: if (m48) s->irq_latch = v; return;
    case 0xC001: if (m48) { s->irq_counter = 0; s->irq_reload = 1; } return;
    case 0xC002: if (m48) s->irq_enable = 1; return;
    case 0xC003: if (m48) { s->irq_enable = 0; cart_irq(c, false); } return;
    case 0xE000: if (m48) s->mirroring = v >> 6; break;
    default: return;
    }
    tc_sync(c);
}
static void tc_ppu_addr(cart_t *c, uint16_t a) {
    taito_state_t *s = &c->s.taito;
    if (c->mapper_id != 48) return;
    if (mapper_a12_edge(&s->wram_en /* reused as a12 state */, a)) {
        if (s->irq_counter == 0 || s->irq_reload) { s->irq_counter = s->irq_latch; s->irq_reload = 0; } else s->irq_counter--;
        if (s->irq_counter == 0 && s->irq_enable) cart_irq(c, true);
    }
}
const mapper_desc_t mapper_033 = { 33, "Taito-TC0190", 0, tc_init, tc_write, NULL, NULL, NULL };
const mapper_desc_t mapper_048 = { 48, "Taito-TC0690", MF_PPU_HOOK, tc_init, tc_write, NULL, tc_ppu_addr, NULL };

/* ---- X1-005 (80 / 207): registers at $7EF0-$7EFF, 128B RAM at $7F00 ---- */
static void x1005_sync(cart_t *c) {
    generic_state_t *g = &c->s.g;
    cart_set_chr2k(c, 0, g->regs[0] >> 1); cart_set_chr2k(c, 1, g->regs[1] >> 1);
    for (unsigned i = 0; i < 4; i++) cart_set_chr1k(c, 4 + i, g->regs[2 + i]);
    cart_set_prg8k(c, 0, g->regs[10]); cart_set_prg8k(c, 1, g->regs[12]); cart_set_prg8k(c, 2, g->regs[14]); cart_set_prg8k(c, 3, -1);
    if (c->mapper_id == 207) { cart_set_nt_ciram(c, 0, g->regs[0] >> 7); cart_set_nt_ciram(c, 1, g->regs[0] >> 7); cart_set_nt_ciram(c, 2, g->regs[1] >> 7); cart_set_nt_ciram(c, 3, g->regs[1] >> 7); }
    else cart_set_mirroring(c, (g->regs[6] & 1) ? MIRROR_V : MIRROR_H);
    cart_unmap_6000(c); /* RAM handled through read/write hooks */
}
static void x1005_init(cart_t *c) { generic_state_t *g = &c->s.g; for (int i = 0; i < 16; i++) g->regs[i] = 0; g->regs[10] = 0; g->regs[12] = 1; g->regs[14] = 2; g->regs[1] = 2; x1005_sync(c); }
static void x1005_write(cart_t *c, uint16_t a, uint8_t v) {
    generic_state_t *g = &c->s.g;
    if (a >= 0x7F00 && a < 0x8000) { if (g->regs[8] == 0xA3 && c->wram) c->wram[a & 0x7F] = v; return; }
    if (a < 0x7EF0 || a > 0x7EFF) return;
    unsigned r = a & 0x0F;
    if (r == 8 || r == 9) { g->regs[8] = v; return; }
    if (r >= 10) g->regs[r & 0x0E] = v;
    else g->regs[r] = v;
    x1005_sync(c);
}
static uint8_t x1005_read(cart_t *c, uint16_t a, uint8_t open) {
    generic_state_t *g = &c->s.g;
    if (a >= 0x7F00 && a < 0x8000 && g->regs[8] == 0xA3 && c->wram) return c->wram[a & 0x7F];
    if (a >= 0x7EF8 && a <= 0x7EF9) return g->regs[8];
    return open;
}
const mapper_desc_t mapper_080 = { 80,  "Taito-X1-005", MF_READ_LOW | MF_WRITE_6000, x1005_init, x1005_write, x1005_read, NULL, NULL };
const mapper_desc_t mapper_207 = { 207, "Taito-X1-005(NT)", MF_READ_LOW | MF_WRITE_6000, x1005_init, x1005_write, x1005_read, NULL, NULL };

/* ---- X1-017 (82) ---- */
static void x1017_sync(cart_t *c) {
    generic_state_t *g = &c->s.g;
    unsigned inv = (g->regs[6] & 2) ? 4 : 0;
    cart_set_chr2k(c, (0 + inv) >> 1, g->regs[0] >> 1); cart_set_chr2k(c, (2 + inv) >> 1, g->regs[1] >> 1);
    for (unsigned i = 0; i < 4; i++) cart_set_chr1k(c, ((4 + i) ^ inv) & 7, g->regs[2 + i]);
    cart_set_prg8k(c, 0, g->regs[10] >> 2); cart_set_prg8k(c, 1, g->regs[11] >> 2); cart_set_prg8k(c, 2, g->regs[12] >> 2); cart_set_prg8k(c, 3, -1);
    cart_set_mirroring(c, (g->regs[6] & 1) ? MIRROR_V : MIRROR_H);
    cart_unmap_6000(c);
}
static void x1017_init(cart_t *c) { generic_state_t *g = &c->s.g; for (int i = 0; i < 16; i++) g->regs[i] = 0; g->regs[11] = 4; g->regs[12] = 8; x1017_sync(c); }
static void x1017_write(cart_t *c, uint16_t a, uint8_t v) {
    generic_state_t *g = &c->s.g;
    if (a >= 0x6000 && a < 0x7EF0) { unsigned blk = (a - 0x6000) >> 11; bool en = (blk == 0 && g->regs[7] == 0xCA) || (blk == 1 && g->regs[8] == 0x69) || (blk == 2 && g->regs[9] == 0x84);
        if (en && c->wram) c->wram[a - 0x6000] = v;
        return; }
    if (a < 0x7EF0 || a > 0x7EFC) return;
    g->regs[a & 0x0F] = v; x1017_sync(c);
}
static uint8_t x1017_read(cart_t *c, uint16_t a, uint8_t open) {
    generic_state_t *g = &c->s.g;
    if (a >= 0x6000 && a < 0x7EF0) { unsigned blk = (a - 0x6000) >> 11; bool en = (blk == 0 && g->regs[7] == 0xCA) || (blk == 1 && g->regs[8] == 0x69) || (blk == 2 && g->regs[9] == 0x84);
        return (en && c->wram) ? c->wram[a - 0x6000] : open; }
    return open;
}
const mapper_desc_t mapper_082 = { 82, "Taito-X1-017", MF_READ_LOW | MF_WRITE_6000, x1017_init, x1017_write, x1017_read, NULL, NULL };
