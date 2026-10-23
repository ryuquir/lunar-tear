/* Discrete-logic and simple-latch boards. Each mapper is a few lines; most use
 * the generic state slot c->s.g. */
#include "../mapper.h"

static uint8_t garbage_page[1024];

/* ---- 0 NROM ---- */
static void nrom_init(cart_t *c) { cart_set_prg32k(c, 0); cart_set_chr8k(c, 0); cart_set_wram_6000(c, 0, true); }
const mapper_desc_t mapper_000 = { 0, "NROM", 0, nrom_init, NULL, NULL, NULL, NULL };

/* ---- 2 UxROM / 94 UN1ROM / 180 UNROM-reverse ---- */
static void uxrom_init(cart_t *c) { cart_set_prg16k(c, 0, 0); cart_set_prg16k(c, 1, -1); cart_set_chr8k(c, 0); cart_set_wram_6000(c, 0, true); }
static void uxrom_write(cart_t *c, uint16_t a, uint8_t v) { (void)a; cart_set_prg16k(c, 0, v); }
const mapper_desc_t mapper_002 = { 2, "UxROM", MF_BUS_CONFLICT, uxrom_init, uxrom_write, NULL, NULL, NULL };
static void un1rom_write(cart_t *c, uint16_t a, uint8_t v) { (void)a; cart_set_prg16k(c, 0, (v >> 2) & 7); }
const mapper_desc_t mapper_094 = { 94, "UN1ROM", MF_BUS_CONFLICT, uxrom_init, un1rom_write, NULL, NULL, NULL };
static void m180_init(cart_t *c) { cart_set_prg16k(c, 0, 0); cart_set_prg16k(c, 1, 0); cart_set_chr8k(c, 0); }
static void m180_write(cart_t *c, uint16_t a, uint8_t v) { (void)a; cart_set_prg16k(c, 1, v & 7); }
const mapper_desc_t mapper_180 = { 180, "UNROM(180)", MF_BUS_CONFLICT, m180_init, m180_write, NULL, NULL, NULL };

/* ---- 3 CNROM / 185 CNROM+security ---- */
static void cnrom_write(cart_t *c, uint16_t a, uint8_t v) { (void)a; cart_set_chr8k(c, v); }
const mapper_desc_t mapper_003 = { 3, "CNROM", MF_BUS_CONFLICT, nrom_init, cnrom_write, NULL, NULL, NULL };
static void m185_apply(cart_t *c, bool en) {
    if (en) cart_set_chr8k(c, 0);
    else for (unsigned i = 0; i < 8; i++) cart_set_chr1k_ptr(c, i, garbage_page, false);
}
static void m185_init(cart_t *c) { nrom_init(c); for (int i = 0; i < 1024; i++) garbage_page[i] = 0xFF; m185_apply(c, true); }
static void m185_write(cart_t *c, uint16_t a, uint8_t v) {
    (void)a; bool en;
    switch (c->submapper) {
    case 4: en = (v & 3) == 0; break; case 5: en = (v & 3) == 1; break;
    case 6: en = (v & 3) == 2; break; case 7: en = (v & 3) == 3; break;
    default: en = (v & 0x0F) != 0 && v != 0x13; break;
    }
    m185_apply(c, en);
}
const mapper_desc_t mapper_185 = { 185, "CNROM+sec", MF_BUS_CONFLICT, m185_init, m185_write, NULL, NULL, NULL };

/* ---- 7 AxROM ---- */
static void axrom_init(cart_t *c) { cart_set_prg32k(c, 0); cart_set_chr8k(c, 0); cart_set_mirroring(c, MIRROR_1A); }
static void axrom_write(cart_t *c, uint16_t a, uint8_t v) { (void)a; cart_set_prg32k(c, v & 7); cart_set_mirroring(c, (v & 0x10) ? MIRROR_1B : MIRROR_1A); }
const mapper_desc_t mapper_007 = { 7, "AxROM", MF_BUS_CONFLICT, axrom_init, axrom_write, NULL, NULL, NULL };

/* ---- 11 Color Dreams ---- */
static void m11_write(cart_t *c, uint16_t a, uint8_t v) { (void)a; cart_set_prg32k(c, v & 3); cart_set_chr8k(c, v >> 4); }
const mapper_desc_t mapper_011 = { 11, "ColorDreams", MF_BUS_CONFLICT, nrom_init, m11_write, NULL, NULL, NULL };

/* ---- 13 CPROM (16K CHR-RAM) ---- */
static void m13_write(cart_t *c, uint16_t a, uint8_t v) { (void)a; cart_set_chr4k(c, 1, v & 3); }
static void m13_init(cart_t *c) { cart_set_prg32k(c, 0); cart_set_chr4k(c, 0, 0); cart_set_chr4k(c, 1, 0); }
const mapper_desc_t mapper_013 = { 13, "CPROM", MF_BUS_CONFLICT, m13_init, m13_write, NULL, NULL, NULL };

/* ---- 34 BNROM / NINA-001 ---- */
static void m34_init(cart_t *c) { nrom_init(c); }
static void m34_write(cart_t *c, uint16_t a, uint8_t v) {
    bool nina = (c->submapper == 1) || (c->submapper == 0 && c->chr_size > 8192);
    if (nina) {
        if (a == 0x7FFD) cart_set_prg32k(c, v & 1);
        else if (a == 0x7FFE) cart_set_chr4k(c, 0, v & 0x0F);
        else if (a == 0x7FFF) cart_set_chr4k(c, 1, v & 0x0F);
        if (a >= 0x6000 && a < 0x8000 && c->prg_wmap[3]) c->prg_wmap[3][a & 0x1FFF] = v;
    } else if (a >= 0x8000) cart_set_prg32k(c, v);
}
const mapper_desc_t mapper_034 = { 34, "BNROM/NINA-001", MF_WRITE_6000, m34_init, m34_write, NULL, NULL, NULL };

/* ---- 66 GxROM ---- */
static void m66_write(cart_t *c, uint16_t a, uint8_t v) { (void)a; cart_set_prg32k(c, (v >> 4) & 3); cart_set_chr8k(c, v & 3); }
const mapper_desc_t mapper_066 = { 66, "GxROM", MF_BUS_CONFLICT, nrom_init, m66_write, NULL, NULL, NULL };

/* ---- 70 / 152 Bandai discrete ---- */
static void m70_init(cart_t *c) { cart_set_prg16k(c, 0, 0); cart_set_prg16k(c, 1, -1); cart_set_chr8k(c, 0); }
static void m70_write(cart_t *c, uint16_t a, uint8_t v) { (void)a; cart_set_prg16k(c, 0, v >> 4); cart_set_chr8k(c, v & 0x0F); }
const mapper_desc_t mapper_070 = { 70, "Bandai-74*161", MF_BUS_CONFLICT, m70_init, m70_write, NULL, NULL, NULL };
static void m152_write(cart_t *c, uint16_t a, uint8_t v) { (void)a; cart_set_prg16k(c, 0, (v >> 4) & 7); cart_set_chr8k(c, v & 0x0F); cart_set_mirroring(c, (v & 0x80) ? MIRROR_1B : MIRROR_1A); }
const mapper_desc_t mapper_152 = { 152, "Bandai-74*161(1scr)", MF_BUS_CONFLICT, m70_init, m152_write, NULL, NULL, NULL };

/* ---- 71 Camerica BF909x ---- */
static void m71_write(cart_t *c, uint16_t a, uint8_t v) {
    if (a >= 0xC000) cart_set_prg16k(c, 0, v);
    else if (a >= 0x8000 && a < 0xA000 && c->submapper == 1) cart_set_mirroring(c, (v & 0x10) ? MIRROR_1B : MIRROR_1A);
}
const mapper_desc_t mapper_071 = { 71, "Camerica", 0, uxrom_init, m71_write, NULL, NULL, NULL };

/* ---- 78 Irem 74*161 (Holy Diver / Cosmo Carrier) ---- */
static void m78_write(cart_t *c, uint16_t a, uint8_t v) {
    (void)a; cart_set_prg16k(c, 0, v & 7); cart_set_chr8k(c, v >> 4);
    if (c->submapper == 3) cart_set_mirroring(c, (v & 8) ? MIRROR_V : MIRROR_H);
    else cart_set_mirroring(c, (v & 8) ? MIRROR_1B : MIRROR_1A);
}
const mapper_desc_t mapper_078 = { 78, "Irem74*161", MF_BUS_CONFLICT, m70_init, m78_write, NULL, NULL, NULL };

/* ---- 79 AVE NINA-03/06 (regs at $4100-$5FFF, A8 set) ---- */
static void m79_write(cart_t *c, uint16_t a, uint8_t v) { if ((a & 0xE100) == 0x4100) { cart_set_prg32k(c, (v >> 3) & 1); cart_set_chr8k(c, v & 7); } }
const mapper_desc_t mapper_079 = { 79, "NINA-03/06", 0, nrom_init, m79_write, NULL, NULL, NULL };

/* ---- 87 Jaleco/Konami 74*139/74 (regs at $6000-$7FFF) ---- */
static void m87_init(cart_t *c) { cart_set_prg32k(c, 0); cart_set_chr8k(c, 0); cart_unmap_6000(c); }
static void m87_write(cart_t *c, uint16_t a, uint8_t v) { if (a >= 0x6000 && a < 0x8000) cart_set_chr8k(c, ((v & 1) << 1) | ((v >> 1) & 1)); }
const mapper_desc_t mapper_087 = { 87, "Jaleco-JF-0x", 0, m87_init, m87_write, NULL, NULL, NULL };

/* ---- 89 / 93 Sunsoft-2 ---- */
static void m89_write(cart_t *c, uint16_t a, uint8_t v) { (void)a; cart_set_prg16k(c, 0, (v >> 4) & 7); cart_set_chr8k(c, ((v >> 4) & 8) | (v & 7)); cart_set_mirroring(c, (v & 8) ? MIRROR_1B : MIRROR_1A); }
const mapper_desc_t mapper_089 = { 89, "Sunsoft-2(3)", MF_BUS_CONFLICT, m70_init, m89_write, NULL, NULL, NULL };
static void m93_write(cart_t *c, uint16_t a, uint8_t v) { (void)a; cart_set_prg16k(c, 0, v >> 4); }
const mapper_desc_t mapper_093 = { 93, "Sunsoft-2(3R)", MF_BUS_CONFLICT, m70_init, m93_write, NULL, NULL, NULL };

/* ---- 184 Sunsoft-1 ---- */
static void m184_init(cart_t *c) { cart_set_prg32k(c, 0); cart_set_chr4k(c, 0, 0); cart_set_chr4k(c, 1, 1); cart_unmap_6000(c); }
static void m184_write(cart_t *c, uint16_t a, uint8_t v) { if (a >= 0x6000 && a < 0x8000) { cart_set_chr4k(c, 0, v & 7); cart_set_chr4k(c, 1, ((v >> 4) & 7) | 4); } }
const mapper_desc_t mapper_184 = { 184, "Sunsoft-1", 0, m184_init, m184_write, NULL, NULL, NULL };

/* ---- 97 Irem TAM-S1 ---- */
static void m97_init(cart_t *c) { cart_set_prg16k(c, 0, -1); cart_set_prg16k(c, 1, 0); cart_set_chr8k(c, 0); }
static void m97_write(cart_t *c, uint16_t a, uint8_t v) {
    (void)a; cart_set_prg16k(c, 1, v & 0x0F);
    static const mirroring_t mm[4] = { MIRROR_1A, MIRROR_H, MIRROR_V, MIRROR_1B };
    cart_set_mirroring(c, mm[v >> 6]);
}
const mapper_desc_t mapper_097 = { 97, "Irem-TAM-S1", 0, m97_init, m97_write, NULL, NULL, NULL };

/* ---- 140 Jaleco JF-11/14 ---- */
static void m140_write(cart_t *c, uint16_t a, uint8_t v) { if (a >= 0x6000 && a < 0x8000) { cart_set_prg32k(c, (v >> 4) & 3); cart_set_chr8k(c, v & 0x0F); } }
const mapper_desc_t mapper_140 = { 140, "Jaleco-JF-11", 0, m87_init, m140_write, NULL, NULL, NULL };

/* ---- 86 Jaleco JF-13 ---- */
static void m86_write(cart_t *c, uint16_t a, uint8_t v) { if (a >= 0x6000 && a < 0x7000) { cart_set_prg32k(c, (v >> 4) & 3); cart_set_chr8k(c, (v & 3) | ((v >> 4) & 4)); } }
const mapper_desc_t mapper_086 = { 86, "Jaleco-JF-13", 0, m87_init, m86_write, NULL, NULL, NULL };

/* ---- 72 / 92 Jaleco JF-17 / JF-19 (latch on D7 / D6 rising) ---- */
static void m72_write(cart_t *c, uint16_t a, uint8_t v) {
    (void)a; uint8_t *last = &c->s.g.regs[0];
    if ((v & 0x80) && !(*last & 0x80)) cart_set_prg16k(c, 0, v & 0x0F);
    if ((v & 0x40) && !(*last & 0x40)) cart_set_chr8k(c, v & 0x0F);
    *last = v;
}
const mapper_desc_t mapper_072 = { 72, "Jaleco-JF-17", MF_BUS_CONFLICT, m70_init, m72_write, NULL, NULL, NULL };
static void m92_init(cart_t *c) { cart_set_prg16k(c, 0, 0); cart_set_prg16k(c, 1, 0); cart_set_chr8k(c, 0); }
static void m92_write(cart_t *c, uint16_t a, uint8_t v) {
    (void)a; uint8_t *last = &c->s.g.regs[0];
    if ((v & 0x80) && !(*last & 0x80)) cart_set_prg16k(c, 1, v & 0x0F);
    if ((v & 0x40) && !(*last & 0x40)) cart_set_chr8k(c, v & 0x0F);
    *last = v;
}
const mapper_desc_t mapper_092 = { 92, "Jaleco-JF-19", MF_BUS_CONFLICT, m92_init, m92_write, NULL, NULL, NULL };
