/* MMC3-based boards: 176 (BMC-FK23C/FK23CA, Waixing FS005/FS006, ...), 37 (PAL-ZZ), 47 (NES-QJ),
 * 189 (TXC PT8154), 361 (YY841101C), 366 (GN-45), 238 (UNL-603-5052), 262 (UNL-SHERO).
 * Register maps checked against https://www.nesdev.org/wiki/INES_Mapper_176, INES_Mapper_037,
 * INES_Mapper_047, INES_Mapper_189, NES_2.0_Mapper_361, NES_2.0_Mapper_366, NES_2.0_Mapper_262 and
 * INES_Mapper_238 (a stub; the protection follows FCEUX boards/603-5052.cpp).
 *
 * All boards reuse the MMC3 core (mmc3.h) for $8000-$FFFF. The core picks variants from the submapper
 * number (1 = MMC6, 3 = MC-ACC, 4 = MMC3A IRQ) which means something else for these mappers, so every
 * init forces the plain MMC3 variant and the IRQ is clocked by mx_ppu_addr (new-style MMC3 counter). */
#include "../mapper.h"
#include "../cartload.h"   /* FC_VIRTUAL_ROM */
#include "mmc3.h"

/* 8 KiB of board CHR-RAM for boards that carry it next to CHR-ROM (FK23CA / SFC-12B / Waixing FS005,
 * Sachen SHERO). Only one mapper is active at a time, so the buffer is shared. */
static uint8_t mx_chrram[8192];

static void mx_init_core(cart_t *c) {
    mmc3_init(c);
    c->s.mmc3.variant = 0;           /* plain MMC3, whatever the submapper number says */
    c->s.mmc3.prg_and = c->s.mmc3.chr_and = 0; c->s.mmc3.prg_or = c->s.mmc3.chr_or = 0;
    mmc3_sync(c);
}

/* A12 rising-edge filter: like mapper_a12_edge(), but a fetch while A12 is already high is not an edge
 * (mapper_a12_edge() tests `state >= 3` with state = 0x80 while high, so it reports an edge on every
 * consecutive high fetch). Low for >= 3 observations before the rise. */
static bool FC_FASTCODE(mx_a12_edge)(uint8_t *state, uint16_t addr) {
    if (addr & 0x1000) {
        bool rise = !(*state & 0x80) && *state >= 3;
        *state = 0x80;
        return rise;
    }
    if (*state & 0x80) *state = 1; else if (*state < 0x7F) (*state)++;
    return false;
}

/* New-style MMC3 IRQ counter, A12 rising edges (needs only A12: fine on rev E U3). */
static void FC_FASTCODE(mx_ppu_addr)(cart_t *c, uint16_t a) {
    mmc3_state_t *s = &c->s.mmc3;
    if (!mx_a12_edge(&s->a12_state, a)) return;
    if (s->irq_counter == 0 || s->irq_reload) { s->irq_counter = s->irq_latch; s->irq_reload = 0; }
    else s->irq_counter--;
    if (s->irq_counter == 0 && s->irq_enable) cart_irq(c, true);
}

/* MMC3 inner 1 KiB CHR bank seen at PPU slot 0..7 (2 KiB regs R0/R1 split into even/odd halves). */
static uint32_t mx_inner_chr(const mmc3_state_t *s, unsigned slot) {
    unsigned j = slot ^ (s->chr_mode ? 4u : 0u);
    if (j < 4) { uint8_t r = s->regs[j >> 1]; return (j & 1) ? (uint32_t)(r | 1) : (uint32_t)(r & ~1u); }
    return s->regs[2 + (j - 4)];
}

/* true when the MMC3 PRG-RAM interface (/WRAM CE + write enable) would pass a $6000-$7FFF write:
 * $A001 bit 7 set (enable) and bit 6 clear (not write-protected). */
static bool mx_wram_wr_enabled(const cart_t *c) { return (c->s.mmc3.wram_ctrl & 0xC0) == 0x80; }

/* Write that also lands in the WRAM mapped at $6000-$7FFF (MF_WRITE_6000 boards with real WRAM). Under
 * FC_VIRTUAL_ROM (rev D) the external RAM chip already took the write. */
static void mx_wram_passthrough(cart_t *c, uint16_t a, uint8_t v) {
#if !FC_VIRTUAL_ROM
    if (a >= 0x6000 && a < 0x8000 && c->prg_wmap[3]) c->prg_wmap[3][a & 0x1FFF] = v;
#else
    (void)c; (void)a; (void)v;
#endif
}

/* =================================================================================================
 * 176 BMC-FK23C / FK23CA (+ Waixing FS005/FS006, JX9003B, GameStar, HST-162)
 *
 * $5000-$5FFF (solder pad 0: the register answers only when A4 is set, mask $5013; pad 0 is the setting
 * nesdev says works for every ROM -- other pad settings select the menu of some multicarts and need a
 * reset button/jumper we do not have):
 *   $5xx0 mode:   bits 2-0 PRG mode (0/1/2 MMC3 512/256/128 KiB, 3 NROM-128, 4 NROM-256, 5 UNROM),
 *                 bit 3 PRG A21 (sub 2), bit 4 CHR outer size (MMC3 256/128 KiB, CNROM 32/16 KiB),
 *                 bit 5 CHR-RAM select (sub 0/1 with both CHR-ROM and CHR-RAM) / NROM-vs-CNROM (sub 1),
 *                 bit 6 CHR A10-A12 from PPU (8 KiB CHR), bit 7 PRG A22 (sub 2)
 *   $5xx1 PRG base A20-A14 (sub 5: A18-A14 only)
 *   $5xx2 CHR base A20-A13 (sub 2: bits 7-6 PRG A24-A23, bit 5 PRG A25; sub 4: bit 7 PRG A21)
 *   $5xx3 bit 1: extended MMC3 mode (regs 8-11: PRG $C000/$E000, CHR $0400/$0C00), sub 0-2
 *   $5xx5 / $5xx6 (sub 3, decode mask $5xx7): PRG A24-A21 / CHR A24-A21
 *   $4800-$4FFF (sub 5): PRG A24-A19
 * $8000-$FFFF MMC3 with mask $E003 ($8002/$8003 etc. are not registers). In UNROM PRG mode the writes
 * set the inner 16 KiB bank (3 bits); in CNROM CHR mode (sub 1) they set the inner 8 KiB CHR bank
 * (2 bits). nesdev does not say whether the MMC3 still sees those writes; like FCEUX we keep them away
 * from the MMC3 so a discrete game's bank writes cannot enable IRQs or flip the mirroring.
 * $A000: bits 1-0 mirroring V/H (sub 2 with $A001.5: 2/3 = single screen).
 * $A001 (sub 2): standard MMC3 until bit 5 is set; then bits 1-0 WRAM bank (32 KiB), bit 2 first 8 KiB
 * of CHR space (1 KiB banks 0-7) is CHR-RAM, bit 6 $5000-$5FFF = outer registers (0: second 4 KiB of
 * WRAM bank 2), bit 7 WRAM enable.
 * Power-on: outer registers 0, extended regs 8-11 = $FE,$FF,$FF,$FF. CHR-RAM next to CHR-ROM is the
 * 8 KiB board RAM (mx_chrram); a pure CHR-RAM cart just banks its own RAM.
 * Not emulated: the $5000-$5FFF WRAM window under FC_VIRTUAL_ROM (rev D keeps WRAM off-chip).
 * ================================================================================================= */
enum { FK_MODE = 0, FK_PRG, FK_CHR, FK_EXT, FK_PRGMSB, FK_CHRMSB, FK_X8, FK_X9, FK_XA, FK_XB, FK_LATCH, FK_A000, FK_A000W };
#define FK(c) ((c)->s.mmc3.ext)

static bool fk_ext(const cart_t *c) { return (FK(c)[FK_EXT] & 0x02) && c->submapper <= 2; }
static bool fk_ramcfg(const cart_t *c) { return c->submapper == 2 && (c->s.mmc3.wram_ctrl & 0x20); }

static void fk_set_chr(cart_t *c, unsigned slot, uint32_t bank) {
    const uint8_t *r = FK(c);
    if (!c->chr_is_ram) {
        bool ram = false;
        if (c->submapper <= 1 && (r[FK_MODE] & 0x60) == 0x20) ram = true;                 /* $5xx0.5: CHR-RAM */
        else if (fk_ramcfg(c) && (c->s.mmc3.wram_ctrl & 0x04) && bank < 8) ram = true;  /* $A001.2: first 8 KiB */
        if (ram) { cart_set_chr1k_ptr(c, slot, mx_chrram + ((bank & 7u) << 10), true); return; }
    }
    cart_set_chr1k(c, slot, (int32_t)bank);
}

static void fk_sync(cart_t *c) {
    mmc3_state_t *s = &c->s.mmc3;
    const uint8_t *r = FK(c);
    uint8_t sub = c->submapper;
    bool ext = fk_ext(c);
    unsigned mode = r[FK_MODE] & 7;

    /* ---- PRG: base in 16 KiB units ---- */
    uint32_t base = r[FK_PRG] & 0x7F;
    switch (sub) {
    case 2: base |= ((r[FK_MODE] & 0x08u) << 4) | ((r[FK_MODE] & 0x80u) << 1) | ((r[FK_CHR] & 0xC0u) << 3) | ((r[FK_CHR] & 0x20u) << 6); break;
    case 3: base |= (r[FK_PRGMSB] & 0x0Fu) << 7; break;
    case 4: base |= r[FK_CHR] & 0x80u; break;
    case 5: base = (r[FK_PRG] & 0x1Fu) | ((r[FK_PRGMSB] & 0x3Fu) << 5); break;
    default: break;
    }
    if (!ext && mode == 3) { cart_set_prg16k(c, 0, (int32_t)base); cart_set_prg16k(c, 1, (int32_t)base); }
    else if (!ext && mode == 4) cart_set_prg32k(c, (int32_t)(base >> 1));
    else if (!ext && mode == 5) {
        cart_set_prg16k(c, 0, (int32_t)((base & ~7u) | (r[FK_LATCH] & 7u)));
        cart_set_prg16k(c, 1, (int32_t)((base & ~7u) | 7u));
    } else {
        uint32_t and_ = ext ? 0xFF : (mode == 1) ? 0x1F : (mode == 2) ? 0x0F : (sub == 1 || sub == 3) ? 0xFF : 0x3F;
        uint32_t or_ = (base << 1) & ~and_;
        uint32_t b[4];
        b[0] = s->regs[6]; b[1] = s->regs[7];
        b[2] = ext ? r[FK_X8] : 0xFFFFFFFEu; b[3] = ext ? r[FK_X9] : 0xFFFFFFFFu;
        if (s->prg_mode) { uint32_t t = b[0]; b[0] = b[2]; b[2] = t; }
        for (unsigned i = 0; i < 4; i++) cart_set_prg8k(c, i, (int32_t)((b[i] & and_) | or_));
    }

    /* ---- CHR: base in 8 KiB units ---- */
    uint32_t cbase = r[FK_CHR];
    if (sub == 3) cbase |= (r[FK_CHRMSB] & 0x0Fu) << 8;
    if (r[FK_MODE] & 0x40) {
        uint32_t b8 = cbase;
        if (sub == 1 && !(r[FK_MODE] & 0x20)) { uint32_t m = (r[FK_MODE] & 0x10) ? 1 : 3; b8 = (cbase & ~m) | (r[FK_LATCH] & m); }
        for (unsigned i = 0; i < 8; i++) fk_set_chr(c, i, b8 * 8 + i);
    } else {
        uint32_t and_ = (r[FK_MODE] & 0x10) ? 0x7F : 0xFF, or_ = (cbase << 3) & ~and_;
        for (unsigned i = 0; i < 8; i++) {
            uint32_t v = mx_inner_chr(s, i);
            if (ext) {
                unsigned j = i ^ (s->chr_mode ? 4u : 0u);
                if (j < 4) v = (j == 0) ? s->regs[0] : (j == 1) ? r[FK_XA] : (j == 2) ? s->regs[1] : r[FK_XB];
            }
            fk_set_chr(c, i, (v & and_) | or_);
        }
    }

    /* ---- WRAM ---- */
    if (c->wram_size == 0) cart_unmap_6000(c);
    else if (fk_ramcfg(c)) { if (s->wram_ctrl & 0x80) cart_set_wram_6000(c, s->wram_ctrl & 3, true); else cart_unmap_6000(c); }
    else if (s->wram_ctrl & 0x80) cart_set_wram_6000(c, 0, !(s->wram_ctrl & 0x40));
    else cart_unmap_6000(c);

    /* ---- mirroring (only once software wrote $A000; before that the header's) ---- */
    if (r[FK_A000W] && c->mirroring != MIRROR_4) {
        uint8_t m = r[FK_A000] & 3;
        if (fk_ramcfg(c) && (m & 2)) cart_set_mirroring(c, (m & 1) ? MIRROR_1B : MIRROR_1A);
        else cart_set_mirroring(c, (m & 1) ? MIRROR_H : MIRROR_V);
    }
}

static void fk_init(cart_t *c) {
    mx_init_core(c);
    uint8_t *r = FK(c);
    for (unsigned i = 0; i < sizeof c->s.mmc3.ext; i++) r[i] = 0;
    r[FK_X8] = 0xFE; r[FK_X9] = 0xFF; r[FK_XA] = 0xFF; r[FK_XB] = 0xFF;
    fk_sync(c);
}

static bool fk_wram_window(const cart_t *c) {   /* sub 2: $A001.5 set, $A001.6 clear => $5000-$5FFF is WRAM */
    return fk_ramcfg(c) && !(c->s.mmc3.wram_ctrl & 0x40);
}

static void fk_write(cart_t *c, uint16_t a, uint8_t v) {
    mmc3_state_t *s = &c->s.mmc3;
    uint8_t *r = FK(c);
    if (a >= 0x5000 && a < 0x6000) {
        if (fk_wram_window(c)) {
#if !FC_VIRTUAL_ROM
            if (c->wram && c->wram_size) c->wram[(0x5000u + (a & 0x0FFFu)) % c->wram_size] = v;
#endif
            return;
        }
        if (!(a & 0x10)) return;                                  /* solder pad 0: A4 must be set */
        unsigned reg = (c->submapper == 3) ? (a & 7u) : (a & 3u);
        switch (reg) {
        case 0: case 1: case 2: case 3: r[reg] = v; break;
        case 5: r[FK_PRGMSB] = v; break;
        case 6: r[FK_CHRMSB] = v; break;
        default: return;
        }
        fk_sync(c);
        return;
    }
    if (a >= 0x4800 && a < 0x5000) { if (c->submapper == 5) { r[FK_PRGMSB] = v; fk_sync(c); } return; }
    if (a < 0x8000) return;
    bool ext = fk_ext(c);
    if (!ext && (r[FK_MODE] & 7) == 5) { r[FK_LATCH] = v; fk_sync(c); return; }                         /* UNROM latch */
    if (c->submapper == 1 && (r[FK_MODE] & 0x60) == 0x40) { r[FK_LATCH] = v; fk_sync(c); return; }      /* CNROM latch */
    if (a & 2) return;                                                                                   /* mask $E003 */
    uint16_t sel = a & 0xE001;
    if (sel == 0x8001 && ext && (s->bank_select & 0x08)) {
        unsigned idx = s->bank_select & 0x0F;
        if (idx < 12) { r[FK_X8 + (idx - 8)] = v; fk_sync(c); }
        return;
    }
    mmc3_write(c, a, v);
    if (sel == 0xA000) { r[FK_A000] = v; r[FK_A000W] = 1; }
    if (sel < 0xC000) fk_sync(c);
}

static uint8_t FC_FASTCODE(fk_read)(cart_t *c, uint16_t a, uint8_t open_bus) {
#if !FC_VIRTUAL_ROM
    if (a >= 0x5000 && a < 0x6000 && fk_wram_window(c) && c->wram && c->wram_size) return c->wram[(0x5000u + (a & 0x0FFFu)) % c->wram_size];
#else
    (void)c; (void)a;
#endif
    return open_bus;
}
const mapper_desc_t mapper_176 = { 176, "BMC-FK23C", MF_PPU_HOOK | MF_READ_LOW, fk_init, fk_write, fk_read, mx_ppu_addr, NULL, NULL };

/* =================================================================================================
 * 37 PAL-ZZ (Super Mario Bros. + Tetris + Nintendo World Cup) and 47 NES-QJ (Super Spike V'Ball +
 * Nintendo World Cup). Outer bank latch at $6000-$7FFF behind the MMC3's PRG-RAM interface: it only
 * latches while $A001 enables and does not write-protect PRG-RAM. No PRG-RAM on either board, the
 * latch is write-only (reads are open bus). Cleared at power-on/reset.
 *   37: [.... .QBB]  PRG: BB=3 -> 64 KiB window with A16 forced high, else A16 = Q & MMC3 A16; A17 = Q.
 *                    CHR: A17 = Q (128 KiB halves).
 *   47: [.... ...B]  128 KiB PRG + 128 KiB CHR block.
 * ================================================================================================= */
static void m37_apply(cart_t *c) {
    mmc3_state_t *s = &c->s.mmc3;
    uint8_t r = s->ext[0];
    if (c->mapper_id == 47) {
        s->prg_and = 0x0F; s->prg_or = (uint16_t)((r & 1u) << 4);
        s->chr_and = 0x7F; s->chr_or = (uint16_t)((r & 1u) << 7);
    } else {
        unsigned q = (r >> 2) & 1, bb = r & 3;
        if (bb == 3) { s->prg_and = 0x07; s->prg_or = (uint16_t)((q << 4) | 0x08); }
        else if (q)  { s->prg_and = 0x0F; s->prg_or = 0x10; }
        else         { s->prg_and = 0x07; s->prg_or = 0x00; }
        s->chr_and = 0x7F; s->chr_or = (uint16_t)(q << 7);
    }
    mmc3_sync(c);
    cart_unmap_6000(c);           /* no PRG-RAM: the PRG-RAM interface drives the latch */
}
static void m37_init(cart_t *c) { mx_init_core(c); c->s.mmc3.ext[0] = 0; m37_apply(c); }
static void m37_write(cart_t *c, uint16_t a, uint8_t v) {
    if (a >= 0x6000 && a < 0x8000) { if (mx_wram_wr_enabled(c)) { c->s.mmc3.ext[0] = v; m37_apply(c); } return; }
    if (a < 0x8000) return;
    mmc3_write(c, a, v);
    if ((a & 0xE001) == 0x8000 || (a & 0xE001) == 0xA001) cart_unmap_6000(c);
}
const mapper_desc_t mapper_037 = { 37, "PAL-ZZ", MF_PPU_HOOK | MF_WRITE_6000, m37_init, m37_write, NULL, mx_ppu_addr, NULL, NULL };
const mapper_desc_t mapper_047 = { 47, "NES-QJ", MF_PPU_HOOK | MF_WRITE_6000, m37_init, m37_write, NULL, mx_ppu_addr, NULL, NULL };

/* =================================================================================================
 * 189 TXC PT8154 (Thunder Warrior, Street Fighter II: The World Warrior, Mario Fighter III).
 * MMC3 clone for CHR, mirroring and IRQ; the MMC3 PRG registers are ignored and a 32 KiB PRG latch is
 * written anywhere in $4020-$7FFF (nesdev's "generalized emulation", which covers the $4100/A8 boards,
 * the oversize board and the $6000 boards): bank = (D >> 4) | (D & $0F). No PRG-RAM. Power-on bank 0.
 * ================================================================================================= */
static void m189_apply(cart_t *c) { cart_set_prg32k(c, c->s.mmc3.ext[0]); cart_unmap_6000(c); }
static void m189_init(cart_t *c) { mx_init_core(c); c->s.mmc3.ext[0] = 0; m189_apply(c); }
static void m189_write(cart_t *c, uint16_t a, uint8_t v) {
    if (a < 0x8000) { c->s.mmc3.ext[0] = (uint8_t)((v >> 4) | (v & 0x0F)); m189_apply(c); return; }
    mmc3_write(c, a, v);
    uint16_t sel = a & 0xE001;
    if (sel == 0x8000 || sel == 0x8001 || sel == 0xA001) m189_apply(c);
}
const mapper_desc_t mapper_189 = { 189, "TXC-PT8154", MF_PPU_HOOK | MF_WRITE_6000, m189_init, m189_write, NULL, mx_ppu_addr, NULL, NULL };

/* =================================================================================================
 * 361 YY841101C (J.Y. Company 4-in-1s, OK-411): $7000-$7FFF [OOOO ....] data bits select the outer
 * 128 KiB PRG + 128 KiB CHR bank. 366 GN-45 (K-3131GS/SS): $6800-$68FF, value from the ADDRESS bus,
 * A~[0110 1000 LOOO ....]: OOO outer 128 KiB PRG + CHR bank, L locks the outer bank until reset.
 * Both registers overlay 8 KiB of WRAM and work whether or not $A001 enables it (the write also lands
 * in WRAM). Exact decode masks are unknown (nesdev); power-on outer bank 0, unlocked.
 * ================================================================================================= */
static void m361_apply(cart_t *c) {
    mmc3_state_t *s = &c->s.mmc3;
    uint8_t o = s->ext[0];
    s->prg_and = 0x0F; s->prg_or = (uint16_t)(o << 4);
    s->chr_and = 0x7F; s->chr_or = (uint16_t)(o << 7);
    mmc3_sync(c);
}
static void m361_init(cart_t *c) { mx_init_core(c); c->s.mmc3.ext[0] = 0; c->s.mmc3.ext[1] = 0; m361_apply(c); }
static void m361_write(cart_t *c, uint16_t a, uint8_t v) {
    mmc3_state_t *s = &c->s.mmc3;
    if (a >= 0x8000) { mmc3_write(c, a, v); return; }
    if (a < 0x6000) return;
    mx_wram_passthrough(c, a, v);
    if (c->mapper_id == 361) {
        if ((a & 0xF000) == 0x7000) { s->ext[0] = v >> 4; m361_apply(c); }
    } else {
        if ((a & 0xFF00) == 0x6800 && !s->ext[1]) { s->ext[0] = (a >> 4) & 7; s->ext[1] = (a >> 7) & 1; m361_apply(c); }
    }
}
const mapper_desc_t mapper_361 = { 361, "YY841101C", MF_PPU_HOOK | MF_WRITE_6000, m361_init, m361_write, NULL, mx_ppu_addr, NULL, NULL };
const mapper_desc_t mapper_366 = { 366, "GN-45", MF_PPU_HOOK | MF_WRITE_6000, m361_init, m361_write, NULL, mx_ppu_addr, NULL, NULL };

/* =================================================================================================
 * 238 UNL-603-5052 (Contra Fighter). Plain MMC3 plus a protection latch over $4020-$7FFF: a write
 * stores LUT[D & 3] (LUT = 0,2,2,3), a read returns the latch (no side effects). No PRG-RAM. Power-on 0.
 * nesdev's page is a stub; behaviour from FCEUX boards/603-5052.cpp.
 * ================================================================================================= */
static void m238_init(cart_t *c) { mx_init_core(c); c->s.mmc3.ext[0] = 0; cart_unmap_6000(c); }
static void m238_write(cart_t *c, uint16_t a, uint8_t v) {
    static const uint8_t lut[4] = { 0x00, 0x02, 0x02, 0x03 };
    if (a < 0x8000) { c->s.mmc3.ext[0] = lut[v & 3]; return; }
    mmc3_write(c, a, v);
    cart_unmap_6000(c);
}
static uint8_t FC_FASTCODE(m238_read)(cart_t *c, uint16_t a, uint8_t open_bus) { (void)a; (void)open_bus; return c->s.mmc3.ext[0]; }
const mapper_desc_t mapper_238 = { 238, "UNL-603-5052", MF_PPU_HOOK | MF_WRITE_6000 | MF_READ_LOW, m238_init, m238_write, m238_read, mx_ppu_addr, NULL, NULL };

/* =================================================================================================
 * 262 UNL-SHERO (Sachen Street Heroes / Shihun). MMC3 plus $4100 (mask probably $C100; we decode
 * $4100-$5FFF with A8 set): write [.M.. 8421]: M = 8 KiB CHR-RAM instead of CHR-ROM; bits 3/2/0/1 add
 * CHR A18 (256 KiB) for PPU $0000-$07FF / $0800-$0FFF / $1000-$17FF / $1800-$1FFF. Read: bit 7 = title
 * jumper (0 = Street Heroes: no jumper fitted), bits 6-0 open bus. Four-screen from the header (the board
 * carries extra VRAM). Power-on $4100 = 0.
 * ================================================================================================= */
static void m262_apply(cart_t *c) {
    mmc3_state_t *s = &c->s.mmc3;
    uint8_t r = s->ext[0];
    if (r & 0x40) {
        if (c->chr_is_ram) cart_set_chr8k(c, 0);
        else for (unsigned i = 0; i < 8; i++) cart_set_chr1k_ptr(c, i, mx_chrram + (i << 10), true);
        return;
    }
    static const uint8_t bit[4] = { 3, 2, 0, 1 };
    for (unsigned i = 0; i < 8; i++) cart_set_chr1k(c, i, (int32_t)(mx_inner_chr(s, i) | (((r >> bit[i >> 1]) & 1u) << 8)));
}
static void m262_init(cart_t *c) { mx_init_core(c); c->s.mmc3.ext[0] = 0; m262_apply(c); }
static void m262_write(cart_t *c, uint16_t a, uint8_t v) {
    if (a < 0x6000) { if ((a & 0xC100) == 0x4100) { c->s.mmc3.ext[0] = v; m262_apply(c); } return; }
    if (a < 0x8000) return;
    mmc3_write(c, a, v);
    uint16_t sel = a & 0xE001;
    if (sel == 0x8000 || sel == 0x8001) m262_apply(c);
}
static uint8_t FC_FASTCODE(m262_read)(cart_t *c, uint16_t a, uint8_t open_bus) {
    (void)c;
    if (a < 0x6000 && (a & 0xC100) == 0x4100) return open_bus & 0x7F;   /* jumper open: Street Heroes */
    return open_bus;
}
const mapper_desc_t mapper_262 = { 262, "UNL-SHERO", MF_PPU_HOOK | MF_READ_LOW, m262_init, m262_write, m262_read, mx_ppu_addr, NULL, NULL };
