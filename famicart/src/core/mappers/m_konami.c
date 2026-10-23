/* Konami: VRC1 (75), VRC2/VRC4 (21/22/23/25), VRC3 (73), VRC6 (24/26), VRC7 (85). */
#include "../mapper.h"
#include "../audio/expaudio.h"

/* ---------- VRC IRQ (shared by VRC4/6/7): 8-bit up counter, scanline or cycle mode ---------- */
typedef struct { uint8_t latch, ctrl, counter; int16_t prescaler; } vrc_irq_t;
static void vrc_irq_write(cart_t *c, vrc_irq_t *q, unsigned reg, uint8_t v) {
    switch (reg) {
    case 0: q->latch = (uint8_t)((q->latch & 0xF0) | (v & 0x0F)); break;
    case 1: q->latch = (uint8_t)((q->latch & 0x0F) | (v << 4)); break;
    case 3: q->latch = v; break;
    case 2: q->ctrl = v & 7; cart_irq(c, false); if (v & 2) { q->counter = q->latch; q->prescaler = 341; } break;
    case 4: cart_irq(c, false); q->ctrl = (uint8_t)((q->ctrl & ~2) | ((q->ctrl & 1) << 1)); break;
    }
}
static void vrc_irq_cycle(cart_t *c, vrc_irq_t *q) {
    if (!(q->ctrl & 2)) return;
    bool clock = false;
    if (q->ctrl & 4) clock = true;
    else { q->prescaler -= 3; if (q->prescaler <= 0) { q->prescaler += 341; clock = true; } }
    if (clock) { if (q->counter == 0xFF) { q->counter = q->latch; cart_irq(c, true); } else q->counter++; }
}

/* ---------- VRC2 / VRC4 ---------- */
static unsigned vrc24_reg(const cart_t *c, uint16_t a) {
    unsigned lo, hi;
    switch (c->mapper_id) {
    case 21: if (c->submapper == 2) { lo = (a >> 6) & 1; hi = (a >> 7) & 1; } else if (c->submapper == 1) { lo = (a >> 1) & 1; hi = (a >> 2) & 1; }
             else { lo = ((a >> 1) | (a >> 6)) & 1; hi = ((a >> 2) | (a >> 7)) & 1; } break;
    case 22: lo = (a >> 1) & 1; hi = a & 1; break;
    case 23: if (c->submapper == 2) { lo = (a >> 2) & 1; hi = (a >> 3) & 1; } else if (c->submapper) { lo = a & 1; hi = (a >> 1) & 1; }
             else { lo = (a | (a >> 2)) & 1; hi = ((a >> 1) | (a >> 3)) & 1; } break;
    default: /* 25 */ if (c->submapper == 2) { lo = (a >> 3) & 1; hi = (a >> 2) & 1; } else if (c->submapper) { lo = (a >> 1) & 1; hi = a & 1; }
             else { lo = ((a >> 1) | (a >> 3)) & 1; hi = (a | (a >> 2)) & 1; } break;
    }
    return lo | (hi << 1);
}
static bool is_vrc2(const cart_t *c) { return c->mapper_id == 22 || (c->mapper_id == 23 && c->submapper == 3) || (c->mapper_id == 25 && c->submapper == 3); }
static void vrc4_sync(cart_t *c) {
    vrc4_state_t *s = &c->s.vrc4;
    if (s->swap_mode & 2) { cart_set_prg8k(c, 0, -2); cart_set_prg8k(c, 2, s->prg[0]); }
    else { cart_set_prg8k(c, 0, s->prg[0]); cart_set_prg8k(c, 2, -2); }
    cart_set_prg8k(c, 1, s->prg[1]); cart_set_prg8k(c, 3, -1);
    for (unsigned i = 0; i < 8; i++) cart_set_chr1k(c, i, c->mapper_id == 22 ? (s->chr[i] >> 1) : s->chr[i]);
    static const mirroring_t mm[4] = { MIRROR_V, MIRROR_H, MIRROR_1A, MIRROR_1B };
    cart_set_mirroring(c, mm[s->mirroring & (is_vrc2(c) ? 1 : 3)]);
    if (c->wram_size) cart_set_wram_6000(c, 0, true); else cart_unmap_6000(c);
}
static void vrc4_init(cart_t *c) {
    vrc4_state_t *s = &c->s.vrc4; s->prg[0] = 0; s->prg[1] = 1; for (int i = 0; i < 8; i++) s->chr[i] = (uint8_t)i; s->swap_mode = 0; s->mirroring = 0;
    s->irq_ctrl = 0; vrc4_sync(c);
}
static void vrc4_write(cart_t *c, uint16_t a, uint8_t v) {
    vrc4_state_t *s = &c->s.vrc4;
    if (a < 0x8000) { if (a >= 0x6000 && is_vrc2(c) && !c->wram_size) s->wram_en = v & 1; return; }
    unsigned r = vrc24_reg(c, a);
    switch (a & 0xF000) {
    case 0x8000: s->prg[0] = v & 0x1F; break;
    case 0x9000: if (r < 2 || is_vrc2(c)) s->mirroring = v & 3; else s->swap_mode = v & 2; break;
    case 0xA000: s->prg[1] = v & 0x1F; break;
    case 0xB000: case 0xC000: case 0xD000: case 0xE000: {
        unsigned idx = (((a >> 12) - 0xB) * 2) + (r >> 1);
        if (r & 1) s->chr[idx] = (uint8_t)((s->chr[idx] & 0x0F) | ((v & 0x1F) << 4)); else s->chr[idx] = (uint8_t)((s->chr[idx] & 0xF0) | (v & 0x0F));
        break; }
    case 0xF000: { vrc_irq_t q = { s->irq_latch, s->irq_ctrl, s->irq_counter, s->prescaler }; vrc_irq_write(c, &q, r == 3 ? 4 : r, v);
                   s->irq_latch = q.latch; s->irq_ctrl = q.ctrl; s->irq_counter = q.counter; s->prescaler = q.prescaler; return; }
    }
    vrc4_sync(c);
}
static uint8_t vrc2_read(cart_t *c, uint16_t a, uint8_t open) { if (a >= 0x6000 && a < 0x7000) return (uint8_t)((open & 0xFE) | (c->s.vrc4.wram_en & 1)); return open; }
static void vrc4_cycle(cart_t *c) { vrc4_state_t *s = &c->s.vrc4; vrc_irq_t q = { s->irq_latch, s->irq_ctrl, s->irq_counter, s->prescaler }; vrc_irq_cycle(c, &q); s->irq_counter = q.counter; s->prescaler = q.prescaler; }
const mapper_desc_t mapper_021 = { 21, "VRC4a/c", MF_CPU_CYCLE, vrc4_init, vrc4_write, NULL, NULL, vrc4_cycle };
const mapper_desc_t mapper_022 = { 22, "VRC2a", MF_READ_LOW | MF_WRITE_6000, vrc4_init, vrc4_write, vrc2_read, NULL, NULL };
const mapper_desc_t mapper_023 = { 23, "VRC2b/4e/4f", MF_CPU_CYCLE | MF_READ_LOW | MF_WRITE_6000, vrc4_init, vrc4_write, vrc2_read, NULL, vrc4_cycle };
const mapper_desc_t mapper_025 = { 25, "VRC2c/4b/4d", MF_CPU_CYCLE | MF_READ_LOW | MF_WRITE_6000, vrc4_init, vrc4_write, vrc2_read, NULL, vrc4_cycle };

/* ---------- VRC1 (75) ---------- */
static void vrc1_sync(cart_t *c) { generic_state_t *g = &c->s.g; cart_set_prg8k(c, 0, g->regs[0]); cart_set_prg8k(c, 1, g->regs[1]); cart_set_prg8k(c, 2, g->regs[2]); cart_set_prg8k(c, 3, -1);
    cart_set_chr4k(c, 0, (g->regs[4] & 0x0F) | ((g->regs[3] & 2) ? 0x10 : 0)); cart_set_chr4k(c, 1, (g->regs[5] & 0x0F) | ((g->regs[3] & 4) ? 0x10 : 0)); cart_set_mirroring(c, (g->regs[3] & 1) ? MIRROR_H : MIRROR_V); }
static void vrc1_init(cart_t *c) { generic_state_t *g = &c->s.g; g->regs[0] = 0; g->regs[1] = 1; g->regs[2] = 2; g->regs[3] = 0; g->regs[4] = 0; g->regs[5] = 1; vrc1_sync(c); }
static void vrc1_write(cart_t *c, uint16_t a, uint8_t v) { generic_state_t *g = &c->s.g;
    switch (a & 0xF000) { case 0x8000: g->regs[0] = v & 0x0F; break; case 0xA000: g->regs[1] = v & 0x0F; break; case 0xC000: g->regs[2] = v & 0x0F; break;
    case 0x9000: g->regs[3] = v & 7; break; case 0xE000: g->regs[4] = v & 0x0F; break; case 0xF000: g->regs[5] = v & 0x0F; break; default: return; } vrc1_sync(c); }
const mapper_desc_t mapper_075 = { 75, "VRC1", 0, vrc1_init, vrc1_write, NULL, NULL, NULL };

/* ---------- VRC3 (73, Salamander) ---------- */
static void vrc3_init(cart_t *c) { cart_set_prg16k(c, 0, 0); cart_set_prg16k(c, 1, -1); cart_set_chr8k(c, 0); cart_set_wram_6000(c, 0, true); c->s.g.r16[0] = 0; c->s.g.regs[0] = 0; }
static void vrc3_write(cart_t *c, uint16_t a, uint8_t v) { generic_state_t *g = &c->s.g;
    switch (a & 0xF000) {
    case 0x8000: g->r16[1] = (uint16_t)((g->r16[1] & 0xFFF0) | (v & 0x0F)); break;
    case 0x9000: g->r16[1] = (uint16_t)((g->r16[1] & 0xFF0F) | ((v & 0x0F) << 4)); break;
    case 0xA000: g->r16[1] = (uint16_t)((g->r16[1] & 0xF0FF) | ((v & 0x0F) << 8)); break;
    case 0xB000: g->r16[1] = (uint16_t)((g->r16[1] & 0x0FFF) | ((v & 0x0F) << 12)); break;
    case 0xC000: g->regs[0] = v & 7; cart_irq(c, false); if (v & 2) g->r16[0] = g->r16[1]; break;
    case 0xD000: cart_irq(c, false); g->regs[0] = (uint8_t)((g->regs[0] & ~2) | ((g->regs[0] & 1) << 1)); break;
    case 0xF000: cart_set_prg16k(c, 0, v & 7); break;
    } }
static void vrc3_cycle(cart_t *c) { generic_state_t *g = &c->s.g; if (!(g->regs[0] & 2)) return;
    if (g->regs[0] & 4) { if ((g->r16[0] & 0xFF) == 0xFF) { g->r16[0] = (uint16_t)((g->r16[0] & 0xFF00) | (g->r16[1] & 0xFF)); cart_irq(c, true); } else g->r16[0]++; }
    else { if (g->r16[0] == 0xFFFF) { g->r16[0] = g->r16[1]; cart_irq(c, true); } else g->r16[0]++; } }
const mapper_desc_t mapper_073 = { 73, "VRC3", MF_CPU_CYCLE, vrc3_init, vrc3_write, NULL, NULL, vrc3_cycle };

/* ---------- VRC6 (24 / 26) ---------- */
static void vrc6_sync(cart_t *c) {
    vrc6_state_t *s = &c->s.vrc6;
    cart_set_prg16k(c, 0, s->prg16); cart_set_prg8k(c, 2, s->prg8); cart_set_prg8k(c, 3, -1);
    switch (s->ctrl & 3) {
    case 0: for (unsigned i = 0; i < 8; i++) cart_set_chr1k(c, i, s->chr[i]); break;
    case 1: for (unsigned i = 0; i < 4; i++) cart_set_chr2k(c, i, s->chr[i]); break;
    default: for (unsigned i = 0; i < 4; i++) cart_set_chr1k(c, i, s->chr[i]); cart_set_chr2k(c, 2, s->chr[4]); cart_set_chr2k(c, 3, s->chr[5]); break;
    }
    static const mirroring_t mm[4] = { MIRROR_V, MIRROR_H, MIRROR_1A, MIRROR_1B };
    cart_set_mirroring(c, mm[(s->ctrl >> 2) & 3]);
    if (s->ctrl & 0x80) cart_set_wram_6000(c, 0, true); else cart_unmap_6000(c);
}
static void vrc6_init(cart_t *c) { vrc6_state_t *s = &c->s.vrc6; s->prg16 = 0; s->prg8 = -2 & 0xFF; for (int i = 0; i < 8; i++) s->chr[i] = (uint8_t)i; s->ctrl = 0; s->irq_ctrl = 0; vrc6_sync(c); cart_set_prg8k(c, 2, -2); }
static void vrc6_write(cart_t *c, uint16_t a, uint8_t v) {
    vrc6_state_t *s = &c->s.vrc6;
    if (a < 0x8000) return;
    if (c->mapper_id == 26) a = (uint16_t)((a & 0xFFFC) | ((a & 1) << 1) | ((a >> 1) & 1));
    switch (a & 0xF003) {
    case 0x8000: case 0x8001: case 0x8002: case 0x8003: s->prg16 = v & 0x0F; break;
    case 0xB003: s->ctrl = v; break;
    case 0xC000: case 0xC001: case 0xC002: case 0xC003: s->prg8 = v & 0x1F; break;
    case 0xD000: case 0xD001: case 0xD002: case 0xD003: s->chr[a & 3] = v; break;
    case 0xE000: case 0xE001: case 0xE002: case 0xE003: s->chr[4 + (a & 3)] = v; break;
    case 0xF000: case 0xF001: case 0xF002: { vrc_irq_t q = { s->irq_latch, s->irq_ctrl, s->irq_counter, s->prescaler }; vrc_irq_write(c, &q, (a & 3) == 0 ? 3 : (a & 3) == 1 ? 2 : 4, v);
                 s->irq_latch = q.latch; s->irq_ctrl = q.ctrl; s->irq_counter = q.counter; s->prescaler = q.prescaler; return; }
    default: return; /* $9000-$B002: audio, handled by the router */
    }
    vrc6_sync(c);
}
static void vrc6_cycle(cart_t *c) { vrc6_state_t *s = &c->s.vrc6; vrc_irq_t q = { s->irq_latch, s->irq_ctrl, s->irq_counter, s->prescaler }; vrc_irq_cycle(c, &q); s->irq_counter = q.counter; s->prescaler = q.prescaler; }
const mapper_desc_t mapper_024 = { 24, "VRC6a", MF_CPU_CYCLE, vrc6_init, vrc6_write, NULL, NULL, vrc6_cycle };
const mapper_desc_t mapper_026 = { 26, "VRC6b", MF_CPU_CYCLE, vrc6_init, vrc6_write, NULL, NULL, vrc6_cycle };

/* ---------- VRC7 (85) ---------- */
static void vrc7_sync(cart_t *c) {
    vrc7_state_t *s = &c->s.vrc7;
    cart_set_prg8k(c, 0, s->prg[0]); cart_set_prg8k(c, 1, s->prg[1]); cart_set_prg8k(c, 2, s->prg[2]); cart_set_prg8k(c, 3, -1);
    for (unsigned i = 0; i < 8; i++) cart_set_chr1k(c, i, s->chr[i]);
    static const mirroring_t mm[4] = { MIRROR_V, MIRROR_H, MIRROR_1A, MIRROR_1B };
    cart_set_mirroring(c, mm[s->mirroring & 3]);
    if (s->mirroring & 0x80) cart_set_wram_6000(c, 0, true); else cart_unmap_6000(c);
}
static void vrc7_init(cart_t *c) { vrc7_state_t *s = &c->s.vrc7; s->prg[0] = 0; s->prg[1] = 1; s->prg[2] = 2; for (int i = 0; i < 8; i++) s->chr[i] = (uint8_t)i; s->mirroring = 0; s->irq_ctrl = 0; vrc7_sync(c); }
static void vrc7_write(cart_t *c, uint16_t a, uint8_t v) {
    vrc7_state_t *s = &c->s.vrc7;
    if (a < 0x8000) return;
    unsigned r = (c->submapper == 1) ? (a >> 3) & 1 : (c->submapper == 2) ? (a >> 4) & 1 : ((a >> 3) | (a >> 4)) & 1;
    switch (a & 0xF000) {
    case 0x8000: s->prg[r] = v & 0x3F; break;
    case 0x9000: if (!r) s->prg[2] = v & 0x3F; else return; /* $9010/$9030 audio */ break;
    case 0xA000: s->chr[r] = v; break;
    case 0xB000: s->chr[2 + r] = v; break;
    case 0xC000: s->chr[4 + r] = v; break;
    case 0xD000: s->chr[6 + r] = v; break;
    case 0xE000: if (!r) s->mirroring = v; else { vrc_irq_t q = { s->irq_latch, s->irq_ctrl, s->irq_counter, s->prescaler }; vrc_irq_write(c, &q, 3, v); s->irq_latch = q.latch; return; } break;
    case 0xF000: { vrc_irq_t q = { s->irq_latch, s->irq_ctrl, s->irq_counter, s->prescaler }; vrc_irq_write(c, &q, r ? 4 : 2, v);
                 s->irq_ctrl = q.ctrl; s->irq_counter = q.counter; s->prescaler = q.prescaler; return; }
    }
    vrc7_sync(c);
}
static void vrc7_cycle(cart_t *c) { vrc7_state_t *s = &c->s.vrc7; vrc_irq_t q = { s->irq_latch, s->irq_ctrl, s->irq_counter, s->prescaler }; vrc_irq_cycle(c, &q); s->irq_counter = q.counter; s->prescaler = q.prescaler; }
const mapper_desc_t mapper_085 = { 85, "VRC7", MF_CPU_CYCLE, vrc7_init, vrc7_write, NULL, NULL, vrc7_cycle };
