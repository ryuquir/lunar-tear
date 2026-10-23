/* MMC3 family: 4 (MMC3/MMC6), 118 (TxSROM), 119 (TQROM), 206/88/95/154/76 (Namcot 108/109/118/119),
 * 37/47 are not included (multicarts). Variant is chosen from mapper id + submapper. */
#include "../mapper.h"

enum { V_MMC3 = 0, V_MMC6, V_TXSROM, V_TQROM, V_MCACC, V_N108, V_N88, V_N95, V_N154, V_N3446 };

static void mmc3_sync_prg(cart_t *c) {
    mmc3_state_t *s = &c->s.mmc3;
    if (s->variant >= V_N108) {
        cart_set_prg8k(c, 0, s->regs[6] & 0x0F); cart_set_prg8k(c, 1, s->regs[7] & 0x0F);
        cart_set_prg8k(c, 2, -2); cart_set_prg8k(c, 3, -1);
        return;
    }
    if (s->prg_mode) { cart_set_prg8k(c, 0, -2); cart_set_prg8k(c, 1, s->regs[7]); cart_set_prg8k(c, 2, s->regs[6]); }
    else             { cart_set_prg8k(c, 0, s->regs[6]); cart_set_prg8k(c, 1, s->regs[7]); cart_set_prg8k(c, 2, -2); }
    cart_set_prg8k(c, 3, -1);
}
static void mmc3_set_chr(cart_t *c, unsigned slot, int32_t bank) {
    mmc3_state_t *s = &c->s.mmc3;
    if (s->variant == V_TQROM) {
        if (bank & 0x40) { /* CHR-RAM 8K */
            uint8_t *ram = c->exram ? c->exram : NULL;
            if (ram) { cart_set_chr1k_ptr(c, slot, ram + (((uint32_t)bank & 7) << 10), true); return; }
        }
        bank &= 0x3F;
    }
    cart_set_chr1k(c, slot, bank);
}
static void mmc3_sync_chr(cart_t *c) {
    mmc3_state_t *s = &c->s.mmc3;
    uint8_t m = s->chr_mode ? 4 : 0;
    if (s->variant == V_N3446) {
        for (unsigned i = 0; i < 4; i++) cart_set_chr2k(c, i, s->regs[2 + i] & 0x3F);
        return;
    }
    int32_t hi = 0;
    for (unsigned i = 0; i < 2; i++) {
        int32_t b = s->regs[i];
        if (s->variant == V_N88 || s->variant == V_N154) b &= 0x3F;           /* lower 64K */
        if (s->variant >= V_N108) b &= 0x3F;
        mmc3_set_chr(c, (m + i * 2) & 7, b & ~1); mmc3_set_chr(c, (m + i * 2 + 1) & 7, b | 1);
    }
    for (unsigned i = 0; i < 4; i++) {
        int32_t b = s->regs[2 + i];
        if (s->variant == V_N88 || s->variant == V_N154) b = (b & 0x3F) | 0x40;  /* upper 64K */
        else if (s->variant >= V_N108) b &= 0x3F;
        mmc3_set_chr(c, ((m ^ 4) + i) & 7, b + hi);
    }
    if (s->variant == V_TXSROM) {   /* nametables from CHR regs bit 7 */
        if (!s->chr_mode) { cart_set_nt_ciram(c, 0, s->regs[0] >> 7); cart_set_nt_ciram(c, 1, s->regs[0] >> 7);
                            cart_set_nt_ciram(c, 2, s->regs[1] >> 7); cart_set_nt_ciram(c, 3, s->regs[1] >> 7); }
        else for (unsigned i = 0; i < 4; i++) cart_set_nt_ciram(c, i, s->regs[2 + i] >> 7);
    } else if (s->variant == V_N95) {
        cart_set_nt_ciram(c, 0, (s->regs[0] >> 5) & 1); cart_set_nt_ciram(c, 1, (s->regs[0] >> 5) & 1);
        cart_set_nt_ciram(c, 2, (s->regs[1] >> 5) & 1); cart_set_nt_ciram(c, 3, (s->regs[1] >> 5) & 1);
    }
}
static void mmc3_sync_wram(cart_t *c) {
    mmc3_state_t *s = &c->s.mmc3;
    if (s->variant >= V_N108) return;
    if (s->variant == V_MMC6) {
        /* MMC6: 1K RAM at $7000-$7FFF (mirrored), bits in $A001 control two 512B halves. */
        if (s->bank_select & 0x20) cart_set_wram_6000(c, 0, (s->wram_ctrl & 0x30) || (s->wram_ctrl & 0xC0));
        else cart_unmap_6000(c);
        return;
    }
    if (c->wram_size == 0) { cart_unmap_6000(c); return; }
    bool en = s->wram_ctrl & 0x80, wp = s->wram_ctrl & 0x40;
    if (c->mapper_id == 4 && c->submapper == 0 && c->wram_size && !en && !wp) en = true; /* MMC3A/early boards: no enable logic */
    if (en) cart_set_wram_6000(c, 0, !wp); else cart_unmap_6000(c);
}
static void mmc3_init(cart_t *c) {
    mmc3_state_t *s = &c->s.mmc3;
    for (int i = 0; i < 8; i++) s->regs[i] = 0;
    s->regs[0] = 0; s->regs[1] = 2; s->regs[2] = 4; s->regs[3] = 5; s->regs[4] = 6; s->regs[5] = 7; s->regs[6] = 0; s->regs[7] = 1;
    s->bank_select = 0; s->prg_mode = 0; s->chr_mode = 0; s->irq_enable = 0; s->irq_counter = 0; s->irq_latch = 0; s->irq_reload = 0;
    s->wram_ctrl = 0x80; s->a12_state = 0;
    switch (c->mapper_id) {
    case 118: s->variant = V_TXSROM; break;
    case 119: s->variant = V_TQROM; break;
    case 206: s->variant = V_N108; break;
    case 88:  s->variant = V_N88; break;
    case 95:  s->variant = V_N95; break;
    case 154: s->variant = V_N154; break;
    case 76:  s->variant = V_N3446; break;
    default:  s->variant = (c->submapper == 1) ? V_MMC6 : (c->submapper == 3) ? V_MCACC : V_MMC3; break;
    }
    mmc3_sync_prg(c); mmc3_sync_chr(c); mmc3_sync_wram(c);
    if (s->variant == V_TXSROM || s->variant == V_N95) { /* nametables from regs */ }
    else if (c->mirroring != MIRROR_4) cart_set_mirroring(c, c->mirroring);
}
static void mmc3_write(cart_t *c, uint16_t a, uint8_t v) {
    mmc3_state_t *s = &c->s.mmc3;
    if (a < 0x8000) return;
    bool namcot = s->variant >= V_N108;
    uint16_t sel = namcot ? (a & 1) : (a & 0xE001);
    if (namcot) {
        if (sel == 0) { s->bank_select = v; if (s->variant == V_N154) cart_set_mirroring(c, (v & 0x40) ? MIRROR_1B : MIRROR_1A); }
        else { s->regs[s->bank_select & 7] = v; mmc3_sync_prg(c); mmc3_sync_chr(c); }
        return;
    }
    switch (sel) {
    case 0x8000: s->bank_select = v; s->prg_mode = (v >> 6) & 1; s->chr_mode = (v >> 7) & 1; mmc3_sync_prg(c); mmc3_sync_chr(c); mmc3_sync_wram(c); break;
    case 0x8001: s->regs[s->bank_select & 7] = v; if ((s->bank_select & 7) < 6) mmc3_sync_chr(c); else mmc3_sync_prg(c); break;
    case 0xA000: if (s->variant != V_TXSROM && s->variant != V_N95 && c->mirroring != MIRROR_4) cart_set_mirroring(c, (v & 1) ? MIRROR_H : MIRROR_V); break;
    case 0xA001: s->wram_ctrl = v; mmc3_sync_wram(c); break;
    case 0xC000: s->irq_latch = v; break;
    case 0xC001: s->irq_counter = 0; s->irq_reload = 1; break;
    case 0xE000: s->irq_enable = 0; cart_irq(c, false); break;
    case 0xE001: s->irq_enable = 1; break;
    }
}
static void mmc3_clock_irq(cart_t *c) {
    mmc3_state_t *s = &c->s.mmc3;
    uint8_t before = s->irq_counter;
    if (s->irq_counter == 0 || s->irq_reload) { s->irq_counter = s->irq_latch; s->irq_reload = 0; }
    else s->irq_counter--;
    bool fire;
    if (c->submapper == 4 || s->variant == V_MCACC) fire = (before != 0 || s->irq_latch != 0) && s->irq_counter == 0; /* "old" MMC3A: 1->0 transition only */
    else fire = s->irq_counter == 0;
    if (fire && s->irq_enable) cart_irq(c, true);
}
static void mmc3_ppu_addr(cart_t *c, uint16_t a) {
    mmc3_state_t *s = &c->s.mmc3;
    if (s->variant >= V_N108) return;
    uint16_t aa = (s->variant == V_MCACC) ? (uint16_t)(a ^ 0x1000) : a;
    if (mapper_a12_edge(&s->a12_state, aa)) mmc3_clock_irq(c);
}
const mapper_desc_t mapper_004 = { 4,   "MMC3",       MF_PPU_HOOK, mmc3_init, mmc3_write, NULL, mmc3_ppu_addr, NULL };
const mapper_desc_t mapper_118 = { 118, "TxSROM",     MF_PPU_HOOK, mmc3_init, mmc3_write, NULL, mmc3_ppu_addr, NULL };
const mapper_desc_t mapper_119 = { 119, "TQROM",      MF_PPU_HOOK, mmc3_init, mmc3_write, NULL, mmc3_ppu_addr, NULL };
const mapper_desc_t mapper_206 = { 206, "Namcot-108", 0, mmc3_init, mmc3_write, NULL, NULL, NULL };
const mapper_desc_t mapper_088 = { 88,  "Namcot-3433", 0, mmc3_init, mmc3_write, NULL, NULL, NULL };
const mapper_desc_t mapper_095 = { 95,  "Namcot-3425", 0, mmc3_init, mmc3_write, NULL, NULL, NULL };
const mapper_desc_t mapper_154 = { 154, "Namcot-3453", 0, mmc3_init, mmc3_write, NULL, NULL, NULL };
const mapper_desc_t mapper_076 = { 76,  "Namcot-3446", 0, mmc3_init, mmc3_write, NULL, NULL, NULL };
