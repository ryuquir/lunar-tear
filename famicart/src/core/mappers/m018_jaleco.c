/* Jaleco SS88006 (mapper 18). */
#include "../mapper.h"
static void ss_sync(cart_t *c) {
    jaleco_state_t *s = &c->s.jaleco;
    for (unsigned i = 0; i < 3; i++) cart_set_prg8k(c, i, s->prg[i]);
    cart_set_prg8k(c, 3, -1);
    for (unsigned i = 0; i < 8; i++) cart_set_chr1k(c, i, s->chr[i]);
    static const mirroring_t mm[4] = { MIRROR_H, MIRROR_V, MIRROR_1A, MIRROR_1B };
    cart_set_mirroring(c, mm[s->mirroring & 3]);
    if (s->irq_mode & 0x80) cart_set_wram_6000(c, 0, true); else cart_unmap_6000(c); /* irq_mode bit7 reused as WRAM enable */
}
static void ss_init(cart_t *c) { jaleco_state_t *s = &c->s.jaleco; s->prg[0] = 0; s->prg[1] = 1; s->prg[2] = 2; for (int i = 0; i < 8; i++) s->chr[i] = (uint8_t)i; s->mirroring = 0; s->irq_enable = 0; s->irq_mode = 0x80; ss_sync(c); }
static inline void nib(uint8_t *r, unsigned hi, uint8_t v) { *r = hi ? (uint8_t)((*r & 0x0F) | (v << 4)) : (uint8_t)((*r & 0xF0) | (v & 0x0F)); }
static void ss_write(cart_t *c, uint16_t a, uint8_t v) {
    jaleco_state_t *s = &c->s.jaleco;
    if (a < 0x8000) return;
    unsigned r = a & 3;
    switch (a & 0xF000) {
    case 0x8000: nib(&s->prg[r >> 1], r & 1, v); break;
    case 0x9000: if (r < 2) nib(&s->prg[2], r & 1, v); else if (r == 2) s->irq_mode = (uint8_t)((s->irq_mode & 0x7F) | ((v & 1) << 7)); break;
    case 0xA000: nib(&s->chr[r >> 1], r & 1, v); break;
    case 0xB000: nib(&s->chr[2 + (r >> 1)], r & 1, v); break;
    case 0xC000: nib(&s->chr[4 + (r >> 1)], r & 1, v); break;
    case 0xD000: nib(&s->chr[6 + (r >> 1)], r & 1, v); break;
    case 0xE000: s->irq_reload = (uint16_t)((s->irq_reload & ~(0xF << (r * 4))) | ((v & 0x0F) << (r * 4))); return;
    case 0xF000:
        switch (r) {
        case 0: s->irq_counter = s->irq_reload; cart_irq(c, false); return;
        case 1: s->irq_enable = v & 1; s->irq_mode = (uint8_t)((s->irq_mode & 0x80) | ((v >> 1) & 7)); cart_irq(c, false); return;
        case 2: s->mirroring = v & 3; break;
        default: return; /* $F003: uPD7756 sample trigger (not emulated) */
        }
        break;
    }
    ss_sync(c);
}
static void ss_cycle(cart_t *c) {
    jaleco_state_t *s = &c->s.jaleco;
    if (!s->irq_enable) return;
    uint16_t mask = (s->irq_mode & 4) ? 0x000F : (s->irq_mode & 2) ? 0x00FF : (s->irq_mode & 1) ? 0x0FFF : 0xFFFF;
    uint16_t cnt = s->irq_counter & mask;
    if (cnt == 0) { cart_irq(c, true); }
    s->irq_counter = (uint16_t)((s->irq_counter & ~mask) | ((cnt - 1) & mask));
}
const mapper_desc_t mapper_018 = { 18, "Jaleco-SS88006", MF_CPU_CYCLE, ss_init, ss_write, NULL, NULL, ss_cycle };
