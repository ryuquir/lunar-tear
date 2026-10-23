/* MMC1 (mapper 1) incl. SUROM/SOROM/SXROM 512K and 16K/32K WRAM variants, submapper 5 (fixed 32K). */
#include "../mapper.h"

static void mmc1_sync(cart_t *c) {
    mmc1_state_t *s = &c->s.mmc1;
    bool big = c->prg_size > 256 * 1024;            /* SUROM/SOROM/SXROM: CHR bit4 selects 256K PRG half */
    uint8_t chr_sel = (s->ctrl & 0x10) ? s->chr0 : s->chr0; /* in 8K mode only chr0 matters */
    int32_t prg_hi = big ? ((chr_sel & 0x10) ? 16 : 0) : 0;
    uint8_t prg = s->prg & 0x0F;
    if (c->submapper == 5) { cart_set_prg32k(c, 0); }
    else switch ((s->ctrl >> 2) & 3) {
    case 0: case 1: cart_set_prg32k(c, (prg_hi + (prg & 0x0E)) >> 1); break;
    case 2: cart_set_prg16k(c, 0, prg_hi); cart_set_prg16k(c, 1, prg_hi + prg); break;
    default: cart_set_prg16k(c, 0, prg_hi + prg); cart_set_prg16k(c, 1, prg_hi + 15); break;
    }
    if (s->ctrl & 0x10) { cart_set_chr4k(c, 0, s->chr0 & 0x1F); cart_set_chr4k(c, 1, s->chr1 & 0x1F); }
    else cart_set_chr8k(c, (s->chr0 & 0x1E) >> 1);
    /* WRAM bank (SOROM 16K: chr bit3, SXROM 32K: chr bits 2-3) */
    uint32_t wbank = 0;
    if (c->wram_size >= 32768) wbank = (chr_sel >> 2) & 3;
    else if (c->wram_size >= 16384) wbank = (chr_sel >> 3) & 1;
    bool wram_en = !(s->prg & 0x10) || c->wram_size == 0;
    if (c->wram_size) cart_set_wram_6000(c, wbank, wram_en); 
    if (!wram_en) cart_unmap_6000(c);
    static const mirroring_t mm[4] = { MIRROR_1A, MIRROR_1B, MIRROR_V, MIRROR_H };
    cart_set_mirroring(c, mm[s->ctrl & 3]);
}
static void mmc1_init(cart_t *c) {
    mmc1_state_t *s = &c->s.mmc1;
    s->shift = 0; s->count = 0; s->ctrl = 0x0C; s->chr0 = s->chr1 = 0; s->prg = 0;
    s->last_write_cycle = 0xFFFFFFFFu;
    mmc1_sync(c);
}
static void mmc1_write(cart_t *c, uint16_t a, uint8_t v) {
    mmc1_state_t *s = &c->s.mmc1;
    if (a < 0x8000) return;
    /* Writes on consecutive CPU cycles are ignored (RMW instructions). */
    if (c->cpu_cycles == s->last_write_cycle + 1) { s->last_write_cycle = c->cpu_cycles; return; }
    s->last_write_cycle = c->cpu_cycles;
    if (v & 0x80) { s->shift = 0; s->count = 0; s->ctrl |= 0x0C; mmc1_sync(c); return; }
    s->shift |= (uint8_t)((v & 1) << s->count);
    if (++s->count == 5) {
        switch ((a >> 13) & 3) {
        case 0: s->ctrl = s->shift & 0x1F; break;
        case 1: s->chr0 = s->shift & 0x1F; break;
        case 2: s->chr1 = s->shift & 0x1F; break;
        default: s->prg = s->shift & 0x1F; break;
        }
        s->shift = 0; s->count = 0;
        mmc1_sync(c);
    }
}
const mapper_desc_t mapper_001 = { 1, "MMC1", 0, mmc1_init, mmc1_write, NULL, NULL, NULL };
