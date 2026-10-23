/* MMC2 (9, Punch-Out!!) and MMC4 (10). The CHR latch flips *after* the triggering fetch. */
#include "../mapper.h"
static void mmc2_sync(cart_t *c) {
    mmc2_state_t *s = &c->s.mmc2;
    cart_set_chr4k(c, 0, s->latch0 ? s->chr_fe0 : s->chr_fd0);
    cart_set_chr4k(c, 1, s->latch1 ? s->chr_fe1 : s->chr_fd1);
}
static void mmc2_init(cart_t *c) {
    mmc2_state_t *s = &c->s.mmc2; s->latch0 = s->latch1 = 1; s->chr_fd0 = s->chr_fe0 = s->chr_fd1 = s->chr_fe1 = 0;
    if (c->mapper_id == 9) { cart_set_prg8k(c, 0, 0); cart_set_prg8k(c, 1, -3); cart_set_prg8k(c, 2, -2); cart_set_prg8k(c, 3, -1); }
    else { cart_set_prg16k(c, 0, 0); cart_set_prg16k(c, 1, -1); cart_set_wram_6000(c, 0, true); }
    mmc2_sync(c);
}
static void mmc2_write(cart_t *c, uint16_t a, uint8_t v) {
    mmc2_state_t *s = &c->s.mmc2;
    switch (a & 0xF000) {
    case 0xA000: if (c->mapper_id == 9) cart_set_prg8k(c, 0, v & 0x0F); else cart_set_prg16k(c, 0, v & 0x0F); break;
    case 0xB000: s->chr_fd0 = v & 0x1F; mmc2_sync(c); break;
    case 0xC000: s->chr_fe0 = v & 0x1F; mmc2_sync(c); break;
    case 0xD000: s->chr_fd1 = v & 0x1F; mmc2_sync(c); break;
    case 0xE000: s->chr_fe1 = v & 0x1F; mmc2_sync(c); break;
    case 0xF000: cart_set_mirroring(c, (v & 1) ? MIRROR_H : MIRROR_V); break;
    }
}
static void mmc2_ppu_addr(cart_t *c, uint16_t a) {
    mmc2_state_t *s = &c->s.mmc2;
    uint8_t *pend = &c->s.raw[200]; /* pending latch change applied after the fetch */
    if (*pend) { if (*pend & 1) s->latch0 = (*pend >> 1) & 1; if (*pend & 4) s->latch1 = (*pend >> 3) & 1; *pend = 0; mmc2_sync(c); }
    if (a < 0x2000) {
        if (c->mapper_id == 9) {
            if (a == 0x0FD8) *pend = 1; else if (a == 0x0FE8) *pend = 1 | 2;
        } else {
            if ((a & 0x1FF8) == 0x0FD8) *pend = 1; else if ((a & 0x1FF8) == 0x0FE8) *pend = 1 | 2;
        }
        if ((a & 0x1FF8) == 0x1FD8) *pend = 4; else if ((a & 0x1FF8) == 0x1FE8) *pend = 4 | 8;
    }
}
const mapper_desc_t mapper_009 = { 9,  "MMC2", MF_PPU_HOOK, mmc2_init, mmc2_write, NULL, mmc2_ppu_addr, NULL };
const mapper_desc_t mapper_010 = { 10, "MMC4", MF_PPU_HOOK, mmc2_init, mmc2_write, NULL, mmc2_ppu_addr, NULL };
