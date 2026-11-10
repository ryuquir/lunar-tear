/* iNES mapper 30: UNROM 512 (nesdev wiki "UNROM 512"). Homebrew board: 16 KB PRG banking over up to 512 KB of flash
 * that the game can re-program, 32 KB CHR-RAM in 8 KB banks, and one register  D[N CC PPPPP]:
 *   PPPPP  16 KB PRG bank at $8000-$BFFF ($C000-$FFFF is fixed to the last 16 KB)
 *   CC     8 KB CHR-RAM bank
 *   N      one-screen page (one-screen boards) or the nametable arrangement (submapper 3)
 * Register decode and bus conflicts by NES 2.0 submapper and the header's battery bit:
 *   sub 0 with battery clear, sub 2      : $8000-$FFFF, bus conflicts
 *   sub 0 with battery set, sub 1, 3, 4  : $C000-$FFFF, no bus conflicts
 * With the battery bit (sub 0, 1, 4) the PRG is flash: writes at $8000-$BFFF are commands to the flash chip, addressed
 * through the bank selected at $8000 (SST39SF040 protocol: 5555/2AAA unlock, byte program, 4 KB sector erase,
 * chip erase, software ID).
 * Nametables come from the header (byte 6 bit 3, bit 0), which rom.c turns into the cart's mirroring:
 *   0,0 / 0,1 fixed arrangement; 1,0 one screen (N selects the CIRAM page); 1,1 four screens taken from the last 8 KB
 *   of CHR-RAM.
 * Not modelled: the LED register of submapper 4; in four-screen mode $3000-$3EFF ("scratch RAM" on the board) reads
 * as a mirror of the nametables. Flash operations complete at once, so the status reads a game polls with see the
 * final data. Re-programmed PRG is changed in RAM (cart.prg_rw) and flagged in prg_dirty for the platform to save. */
#include "../mapper.h"

enum { NT_FIXED = 0, NT_ONE, NT_FOUR, NT_REG };
enum { F_CMD = 0, F_PROGRAM, F_ERASE };
#define ID_PAGE (cart_aux_ram())            /* 8 KB shown instead of PRG while the flash is in software-ID mode */

static void m30_apply(cart_t *c) {
    m030_state_t *s = &c->s.m030;
    if (s->f_id) { for (unsigned i = 4; i < 8; i++) c->prg_map[i] = ID_PAGE; c->tables_dirty = 1; }
    else { cart_set_prg16k(c, 0, s->reg & 0x1F); cart_set_prg16k(c, 1, -1); }
    cart_set_chr8k(c, (s->reg >> 5) & 3);
    if (s->ntmode == NT_ONE) cart_set_mirroring(c, (s->reg & 0x80) ? MIRROR_1B : MIRROR_1A);
    else if (s->ntmode == NT_REG) cart_set_mirroring(c, (s->reg & 0x80) ? MIRROR_V : MIRROR_H);
}

static void m30_init(cart_t *c) {
    m030_state_t *s = &c->s.m030;
    uint8_t sub = c->submapper;
    s->split = (sub == 1 || sub == 3 || sub == 4 || (sub == 0 && c->battery)) ? 1 : 0;
    s->flash = (c->battery && (sub == 0 || sub == 1 || sub == 4)) ? 1 : 0;
    c->bus_conflicts = !s->split;
    s->ntmode = (sub == 3) ? NT_REG : (c->mirroring == MIRROR_4) ? NT_FOUR
              : (c->mirroring == MIRROR_1A || c->mirroring == MIRROR_1B) ? NT_ONE : NT_FIXED;
    for (unsigned i = 0; i < CART_AUX_RAM_SIZE; i++) ID_PAGE[i] = (i & 1) ? 0xB7 : 0xBF;   /* SST manufacturer, SST39SF040 */
    cart_unmap_6000(c);                                   /* the board has no PRG-RAM */
    if (s->ntmode == NT_FOUR && c->chr_is_ram && c->chr_size >= 8192)
        for (unsigned nt = 0; nt < 4; nt++) cart_set_nt_ptr(c, nt, c->chr + c->chr_size - 8192 + nt * 1024u);
    m30_apply(c);
}

static void m30_flash_reset(m030_state_t *s) { s->f_mode = F_CMD; s->f_step = 0; }

static void m30_flash(cart_t *c, uint16_t a, uint8_t v) {
    m030_state_t *s = &c->s.m030;
    uint32_t fa = ((uint32_t)(s->reg & 0x1F) << 14) | (a & 0x3FFFu);    /* address at the flash chip */
    uint32_t cmd = fa & 0x7FFF;
    uint8_t *rw = c->prg_rw; uint32_t size = c->prg_size;
    switch (s->f_mode) {
    case F_CMD:
        if (s->f_step == 0) {
            if (cmd == 0x5555 && v == 0xAA) s->f_step = 1;
            else if (v == 0xF0 && s->f_id) { s->f_id = 0; m30_apply(c); }
        } else if (s->f_step == 1) {
            s->f_step = (cmd == 0x2AAA && v == 0x55) ? 2 : 0;
        } else {
            s->f_step = 0;
            if (cmd != 0x5555) break;
            if (v == 0x80) { s->f_mode = F_ERASE; s->f_step = 3; }
            else if (v == 0xA0) s->f_mode = F_PROGRAM;
            else if (v == 0x90) { s->f_id = 1; m30_apply(c); }
            else if (v == 0xF0 && s->f_id) { s->f_id = 0; m30_apply(c); }
        }
        break;
    case F_PROGRAM:                                        /* programming can only clear bits */
        if (rw && size) { rw[fa % size] &= v; s->prg_dirty = 1; }
        m30_flash_reset(s);
        break;
    case F_ERASE:
        if (s->f_step == 3) { if (cmd == 0x5555 && v == 0xAA) s->f_step = 4; else m30_flash_reset(s); }
        else if (s->f_step == 4) { if (cmd == 0x2AAA && v == 0x55) s->f_step = 5; else m30_flash_reset(s); }
        else {
            if (rw && size) {
                if (v == 0x30) { uint32_t base = (fa % size) & ~0xFFFu; for (uint32_t i = 0; i < 4096 && base + i < size; i++) rw[base + i] = 0xFF; s->prg_dirty = 1; }
                else if (v == 0x10 && cmd == 0x5555) { for (uint32_t i = 0; i < size; i++) rw[i] = 0xFF; s->prg_dirty = 1; }
            }
            m30_flash_reset(s);
        }
        break;
    }
}

static void m30_write(cart_t *c, uint16_t a, uint8_t v) {
    m030_state_t *s = &c->s.m030;
    if (a < 0x8000) return;
    if (s->split && a < 0xC000) { if (s->flash) m30_flash(c, a, v); return; }   /* (sub 4 without flash: LED register) */
    s->reg = v;
    m30_apply(c);
}
const mapper_desc_t mapper_030 = { 30, "UNROM 512", MF_BUS_CONFLICT, m30_init, m30_write, NULL, NULL, NULL, NULL };
