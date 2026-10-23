/* Tengen RAMBO-1 (64). */
#include "../mapper.h"
static void rb_sync(cart_t *c) {
    rambo1_state_t *s = &c->s.rambo1;
    uint8_t m = (s->bank & 0x80) ? 4 : 0;
    if (s->bank & 0x20) { for (unsigned i = 0; i < 2; i++) { cart_set_chr1k(c, (m + i * 2) & 7, s->chr[i]); cart_set_chr1k(c, (m + i * 2 + 1) & 7, s->chr[6 + i]); } }
    else for (unsigned i = 0; i < 2; i++) { cart_set_chr1k(c, (m + i * 2) & 7, s->chr[i] & ~1); cart_set_chr1k(c, (m + i * 2 + 1) & 7, s->chr[i] | 1); }
    for (unsigned i = 0; i < 4; i++) cart_set_chr1k(c, ((m ^ 4) + i) & 7, s->chr[2 + i]);
    if (s->bank & 0x40) { cart_set_prg8k(c, 0, s->prg[2]); cart_set_prg8k(c, 1, s->prg[0]); cart_set_prg8k(c, 2, s->prg[1]); }
    else { cart_set_prg8k(c, 0, s->prg[0]); cart_set_prg8k(c, 1, s->prg[1]); cart_set_prg8k(c, 2, s->prg[2]); }
    cart_set_prg8k(c, 3, -1);
    cart_set_mirroring(c, s->mirroring ? MIRROR_H : MIRROR_V);
}
static void rb_init(cart_t *c) { rambo1_state_t *s = &c->s.rambo1; s->bank = 0; for (int i = 0; i < 8; i++) s->chr[i] = (uint8_t)i; s->prg[0] = 0; s->prg[1] = 1; s->prg[2] = 2; s->mirroring = 0; s->irq_enable = 0; rb_sync(c); }
static void rb_write(cart_t *c, uint16_t a, uint8_t v) {
    rambo1_state_t *s = &c->s.rambo1; if (a < 0x8000) return;
    switch (a & 0xE001) {
    case 0x8000: s->bank = v; break;
    case 0x8001: { unsigned r = s->bank & 0x0F; if (r < 6) s->chr[r] = v; else if (r == 6 || r == 7) s->prg[r - 6] = v; else if (r == 8 || r == 9) s->chr[6 + (r - 8)] = v; else if (r == 0xF) s->prg[2] = v; } break;
    case 0xA000: s->mirroring = v & 1; break;
    case 0xC000: s->irq_latch = v; return;
    case 0xC001: s->irq_reload = 1; s->irq_mode = v & 1; s->irq_counter = 0; return;
    case 0xE000: s->irq_enable = 0; cart_irq(c, false); return;
    case 0xE001: s->irq_enable = 1; return;
    }
    rb_sync(c);
}
static void rb_clock(cart_t *c) {
    rambo1_state_t *s = &c->s.rambo1;
    if (s->irq_reload) { s->irq_counter = s->irq_latch ? (uint8_t)(s->irq_latch | 1) : 0; s->irq_reload = 0; }
    else if (s->irq_counter == 0) s->irq_counter = s->irq_latch; else s->irq_counter--;
    if (s->irq_counter == 0 && s->irq_enable) s->irq_delay = 3;   /* RAMBO-1 asserts a few cycles late */
}
static void rb_ppu_addr(cart_t *c, uint16_t a) { rambo1_state_t *s = &c->s.rambo1; if (s->irq_mode) return; if (mapper_a12_edge(&s->a12_state, a)) rb_clock(c); }
static void rb_cycle(cart_t *c) { rambo1_state_t *s = &c->s.rambo1;
    if (s->irq_delay) { if (--s->irq_delay == 0) cart_irq(c, true); }
    if (s->irq_mode) { if (++s->prg_mode >= 4) { s->prg_mode = 0; rb_clock(c); } } }   /* prg_mode doubles as the /4 prescaler */
const mapper_desc_t mapper_064 = { 64, "Tengen-RAMBO-1", MF_PPU_HOOK | MF_CPU_CYCLE, rb_init, rb_write, NULL, rb_ppu_addr, rb_cycle };
