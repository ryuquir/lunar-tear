/* Namco 129/163 (19) and Namco 175/340 (210). Audio RAM is shared with the expansion-audio layer. */
#include "../mapper.h"
#include "../audio/expaudio.h"
extern uint8_t expaudio_regs_n163[128];

static void n163_sync(cart_t *c) {
    n163_state_t *s = &c->s.n163;
    for (unsigned i = 0; i < 3; i++) cart_set_prg8k(c, i, s->prg[i] & 0x3F);
    cart_set_prg8k(c, 3, -1);
    for (unsigned i = 0; i < 8; i++) {
        uint8_t b = s->chr[i];
        bool ram_ok = (i < 4) ? !(s->chr_ram_lo) : !(s->chr_ram_hi);
        if (c->mapper_id == 19 && b >= 0xE0 && ram_ok) { /* CIRAM as CHR: not routable to the cartridge; use local extvram if present */
            if (c->extvram) cart_set_chr1k_ptr(c, i, c->extvram + ((b & 1) << 10), true); else cart_set_chr1k(c, i, b);
        } else cart_set_chr1k(c, i, b);
    }
    if (c->mapper_id == 19) {
        for (unsigned i = 0; i < 4; i++) { uint8_t b = s->nt[i]; if (b >= 0xE0) cart_set_nt_ciram(c, i, b & 1); else cart_set_nt_chr1k(c, i, b); }
    } else if (c->submapper == 2) {
        static const mirroring_t mm[4] = { MIRROR_1A, MIRROR_V, MIRROR_H, MIRROR_1B };
        cart_set_mirroring(c, mm[s->prg[0] >> 6]);
    }
    if (c->wram_size) cart_set_wram_6000(c, 0, c->mapper_id == 19 ? true : (s->ram_wren & 1)); else cart_unmap_6000(c);
}
static void n163_init(cart_t *c) {
    n163_state_t *s = &c->s.n163; s->prg[0] = 0; s->prg[1] = 1; s->prg[2] = 2; for (int i = 0; i < 8; i++) s->chr[i] = (uint8_t)i;
    s->nt[0] = 0xE0; s->nt[1] = 0xE1; s->nt[2] = 0xE0; s->nt[3] = 0xE1; s->irq_enable = false; s->irq_counter = 0; s->ram_wren = 0; s->chr_ram_lo = s->chr_ram_hi = 0;
    if (c->mapper_id == 210 && c->submapper != 2) cart_set_mirroring(c, c->mirroring);
    n163_sync(c);
}
static void n163_write(cart_t *c, uint16_t a, uint8_t v) {
    n163_state_t *s = &c->s.n163;
    if (c->mapper_id == 19) {
        if ((a & 0xF800) == 0x4800) { if (c->exram) c->exram[s->ram_addr & 0x7F] = v; if (s->ram_inc) s->ram_addr = (s->ram_addr + 1) & 0x7F; return; }
        if ((a & 0xF800) == 0x5000) { s->irq_counter = (uint16_t)((s->irq_counter & 0x7F00) | v); cart_irq(c, false); return; }
        if ((a & 0xF800) == 0x5800) { s->irq_counter = (uint16_t)((s->irq_counter & 0x00FF) | ((v & 0x7F) << 8)); s->irq_enable = v >> 7; cart_irq(c, false); return; }
        if (a >= 0x6000 && a < 0x8000) { if (c->wram && !(s->ram_wren & 0x40) /* write protect bits */) c->wram[a & 0x1FFF] = v; return; }
    }
    if (a < 0x8000) { if (c->mapper_id == 210 && (a & 0xF800) == 0xC000) s->ram_wren = v; return; }
    switch (a & 0xF800) {
    case 0x8000: case 0x8800: case 0x9000: case 0x9800: case 0xA000: case 0xA800: case 0xB000: case 0xB800:
        s->chr[(a - 0x8000) >> 11] = v; break;
    case 0xC000: case 0xC800: case 0xD000: case 0xD800:
        if (c->mapper_id == 19) s->nt[(a - 0xC000) >> 11] = v; else if (a < 0xC800) s->ram_wren = v; break;
    case 0xE000: s->prg[0] = v; break;              /* bit6: sound disable (router), bits6-7: 340 mirroring */
    case 0xE800: s->prg[1] = v; s->chr_ram_lo = (v >> 6) & 1; s->chr_ram_hi = (v >> 7) & 1; break;
    case 0xF000: s->prg[2] = v; break;
    case 0xF800: if (c->mapper_id == 19) { s->ram_addr = v & 0x7F; s->ram_inc = v >> 7; s->ram_wren = (uint8_t)(v & 0x40 ? 0x40 : 0); return; } break;
    }
    n163_sync(c);
}
static uint8_t n163_read(cart_t *c, uint16_t a, uint8_t open) {
    n163_state_t *s = &c->s.n163;
    if (c->mapper_id != 19) return open;
    if ((a & 0xF800) == 0x4800) { uint8_t v = c->exram ? c->exram[s->ram_addr & 0x7F] : 0; if (s->ram_inc) s->ram_addr = (s->ram_addr + 1) & 0x7F; return v; }
    if ((a & 0xF800) == 0x5000) return (uint8_t)(s->irq_counter & 0xFF);
    if ((a & 0xF800) == 0x5800) return (uint8_t)((s->irq_counter >> 8) | (s->irq_enable << 7));
    return open;
}
static void n163_cycle(cart_t *c) {
    n163_state_t *s = &c->s.n163;
    if (!s->irq_enable || s->irq_counter >= 0x7FFF) return;
    if (++s->irq_counter == 0x7FFF) cart_irq(c, true);
}
const mapper_desc_t mapper_019 = { 19,  "Namco-163", MF_CPU_CYCLE | MF_READ_LOW | MF_WRITE_6000, n163_init, n163_write, n163_read, NULL, n163_cycle };
const mapper_desc_t mapper_210 = { 210, "Namco-175/340", 0, n163_init, n163_write, NULL, NULL, NULL };
