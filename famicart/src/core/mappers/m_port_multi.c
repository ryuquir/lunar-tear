/* Multicart / discrete-logic boards: 59 (BMC-T3H53 / BMC-D1038), 41 (Caltron 6-in-1), 228 (Action 52 /
 * Cheetahmen II), 217 (BMC 255-in-1 / 500-in-1, MMC3-based), 232 (Camerica BF9096 / Quattro),
 * 234 (AVE Maxi 15), 27 (World Hero VRC4 clone, plus the CC-21 "Mi Hun Che" reassignment), 521 (DREAMTECH01).
 *
 * Register maps checked against https://www.nesdev.org/wiki/INES_Mapper_059, _041, _228, _217, _232, _234, _027
 * and https://www.nesdev.org/wiki/NES_2.0_Mapper_521. Where the wiki is silent (217 is a one-line stub there,
 * 232 submapper 1, 27's IRQ style) the behavior follows Mesen2 (and FCEUX for CC-21); see each section.
 *
 * ---- Firmware hook for mapper 234 (AVE Maxi 15) ----
 * The Maxi 15 registers at $FF80-$FF9F and $FFE8-$FFF7 latch the byte that was READ from ROM at those addresses
 * (that is how the games bankswitch without bus conflicts). The core's cart_cpu_read() never calls
 * mapper->read() for mapped ROM, so this file exports
 *     void m234_rom_read(cart_t *c, uint16_t a);            -- call after the CPU read ROM address a
 *     void m234_latch(cart_t *c, uint16_t a, uint8_t v);    -- same, when the caller already has the byte v
 * The firmware must call one of them for every confirmed CPU read of $FF80-$FF9F / $FFE8-$FFF7 (other addresses
 * are ignored, so calling it for every $8000-$FFFF read is fine). mapper_234.read() does the same for an
 * address >= $8000 and returns the ROM byte, mapper_234.peek() returns the byte without latching.
 * Limitation on rev E: U1's read confirmation (reve/rcommit.h) only commits reads made while /ROMSEL stayed high,
 * so $FFxx reads are not confirmed at all today; once wired, the bank change is applied when the read is
 * confirmed, i.e. after the bus cycle and later than on the real board (the real latch switches at the end of
 * the read cycle). Code that bankswitches while executing from the switched 32 KiB window could fetch a few
 * bytes from the old bank. The Maxi 15 menu switches from RAM / from the register table, which tolerates that.
 * Writes to the same registers also latch (with bus conflicts, MF_BUS_CONFLICT) and work on every revision. */
#include "../mapper.h"
#include "../cartload.h"   /* FC_VIRTUAL_ROM */
#include "mmc3.h"

void m234_rom_read(cart_t *c, uint16_t a);
void m234_latch(cart_t *c, uint16_t a, uint8_t v);

/* ======================================================================================================
 * 59  UNL-D1038 / BMC-T3H53 (address latch at $8000-$FFFF)
 *   A~[1... ..LD SPPp MCCC]  CCC = 8K CHR, M = mirroring (0 V, 1 H), PPp = 16K PRG bank,
 *   S = 0: p replaced by CPU A14 (NROM-256, 32K bank PP), 1: NROM-128 (16K bank PPp at both halves),
 *   D = 1: reads of $8000-$FFFF return the jumper value in D1-D0 (rest open bus), L = lock until reset.
 *   No bus conflicts documented. Power-on/reset: latch 0 (32K bank 0, CHR 0, vertical).
 *   Jumper: the board's solder jumper is "nothing fitted" = 0. The jumper reads are served from a constant
 *   8 KiB page of zeros mapped over $8000-$FFFF (const, lives in flash), so they work on every bus front-end
 *   (rev E U1 serves it like ROM); the open-bus upper bits read as 0. (rev D's external flash cannot serve a
 *   core-side page: there the jumper read returns the boot bank instead.)
 * ====================================================================================================== */
#define M59_JUMPER 0   /* must stay 0: m59_jumper_page is zero-initialised */
static const uint8_t m59_jumper_page[8192];
static void m59_sync(cart_t *c) {
    uint16_t l = c->s.g.r16[0];
    if (l & 0x80) { cart_set_prg16k(c, 0, (l >> 4) & 7); cart_set_prg16k(c, 1, (l >> 4) & 7); }
    else cart_set_prg32k(c, (l >> 5) & 3);
    cart_set_chr8k(c, l & 7);
    cart_set_mirroring(c, (l & 8) ? MIRROR_H : MIRROR_V);
    if (l & 0x100) {
        for (unsigned i = 4; i < 8; i++) { c->prg_map[i] = m59_jumper_page; c->prg_wmap[i] = NULL; }
        c->tables_dirty = 1;
    }
}
static void m59_init(cart_t *c) { c->s.g.r16[0] = 0; cart_unmap_6000(c); m59_sync(c); }
static void m59_write(cart_t *c, uint16_t a, uint8_t v) {
    (void)v;
    if (a < 0x8000 || (c->s.g.r16[0] & 0x200)) return;   /* locked until reset */
    c->s.g.r16[0] = a & 0x3FF;
    m59_sync(c);
}
const mapper_desc_t mapper_059 = { 59, "BMC-T3H53/D1038", 0, m59_init, m59_write, NULL, NULL, NULL, NULL };

/* ======================================================================================================
 * 41  Caltron 6-in-1
 *   $6000-$67FF (address lines, mask $F800): A~[0110 0... ..MC CEPP]  EPP = 32K PRG bank (A2-A0),
 *   CC = 32K outer CHR bank, M = mirroring (0 V, 1 H). E (= PRG bank 4-7) enables the inner register.
 *   $8000-$FFFF (bus conflicts): D~[..ZZ ..cc] cc = 8K inner CHR bank, written only while E = 1.
 *   No PRG RAM. Both registers cleared at power-up/reset.
 * ====================================================================================================== */
static void m41_sync(cart_t *c) {
    uint8_t o = c->s.g.regs[0], in = c->s.g.regs[1];
    cart_set_prg32k(c, o & 7);
    cart_set_chr8k(c, (int32_t)((((o >> 3) & 3u) << 2) | (in & 3u)));
    cart_set_mirroring(c, (o & 0x20) ? MIRROR_H : MIRROR_V);
}
static void m41_init(cart_t *c) { c->s.g.regs[0] = 0; c->s.g.regs[1] = 0; cart_unmap_6000(c); m41_sync(c); }
static void m41_write(cart_t *c, uint16_t a, uint8_t v) {
    if ((a & 0xF800) == 0x6000) c->s.g.regs[0] = (uint8_t)(a & 0x3F);
    else if (a >= 0x8000 && (c->s.g.regs[0] & 4)) c->s.g.regs[1] = v & 3;
    else return;
    m41_sync(c);
}
const mapper_desc_t mapper_041 = { 41, "Caltron6in1", MF_WRITE_6000 | MF_BUS_CONFLICT, m41_init, m41_write, NULL, NULL, NULL, NULL };

/* ======================================================================================================
 * 228  Active Enterprises (Action 52, Cheetahmen II)
 *   $8000-$FFFF: A~[1.MH HPPP PPS. CCCC]  D~[.... ..cc]
 *   M = mirroring (0 V, 1 H); HH = 512K PRG chip; PPPPP = 16K bank in the chip; S = 0: 32K (bank&~1 at $8000,
 *   bank|1 at $C000), 1: same 16K bank at both; 8K CHR = CCCC cc.
 *   Action 52 has chips 0, 1 and 3 (the file is 1.5 MiB with chip 3 stored third); chip 2 is open bus:
 *   $8000-$FFFF is unmapped then and read() returns open bus. Games expect $00 written to $8000 at power-on,
 *   so init applies that write. No bus conflicts.
 *   $4020-$5FFF: four 4-bit RAM cells ($4020-$4023, mirrored). The wiki says neither cartridge really has it and
 *   no game uses it; it is emulated anyway (D3-D0, upper bits open bus). On rev E U1 only drives mapper reads at
 *   $6000+, so these cells read as open bus there.
 * ====================================================================================================== */
static void m228_sync(cart_t *c) {
    uint16_t a = c->s.g.r16[0]; uint8_t d = c->s.g.regs[0];
    unsigned chip = (a >> 11) & 3;
    bool a52 = c->prg_size == 3u * 512u * 1024u;
    if (a52 && chip == 2) {
        for (unsigned i = 4; i < 8; i++) { c->prg_map[i] = NULL; c->prg_wmap[i] = NULL; }
        c->tables_dirty = 1;
    } else {
        if (a52 && chip == 3) chip = 2;
        int32_t b = (int32_t)((chip << 5) | ((a >> 6) & 0x1F));
        if (a & 0x20) { cart_set_prg16k(c, 0, b); cart_set_prg16k(c, 1, b); }
        else { cart_set_prg16k(c, 0, b & ~1); cart_set_prg16k(c, 1, b | 1); }
    }
    cart_set_chr8k(c, (int32_t)(((a & 0x0Fu) << 2) | (d & 3u)));
    cart_set_mirroring(c, (a & 0x2000) ? MIRROR_H : MIRROR_V);
}
static void m228_init(cart_t *c) {
    for (unsigned i = 0; i < 4; i++) c->s.g.regs[4 + i] = 0;
    c->s.g.r16[0] = 0x8000; c->s.g.regs[0] = 0; cart_unmap_6000(c); m228_sync(c);
}
static void m228_write(cart_t *c, uint16_t a, uint8_t v) {
    if (a >= 0x8000) { c->s.g.r16[0] = a; c->s.g.regs[0] = v; m228_sync(c); }
    else if (a >= 0x4020 && a < 0x6000) c->s.g.regs[4 + (a & 3)] = v & 0x0F;
}
static uint8_t FC_FASTCODE(m228_read)(cart_t *c, uint16_t a, uint8_t open) {
    if (a >= 0x4020 && a < 0x6000) return (uint8_t)((open & 0xF0) | c->s.g.regs[4 + (a & 3)]);
    return open;   /* $6000-$7FFF (no RAM) and the missing chip 2 */
}
const mapper_desc_t mapper_228 = { 228, "ActionEnterprises", MF_READ_LOW, m228_init, m228_write, m228_read, NULL, NULL, NULL };

/* ======================================================================================================
 * 217  BMC 255-in-1 / 500-in-1 / 2000-in-1 (MMC3 with scrambled registers)
 *   nesdev's page is a one-line stub; this follows Mesen2 (MMC3_217). FCEUX later reassigned 217 to a
 *   discrete-latch board; that variant is not implemented.
 *   $5000: E0  D7 = 1: NROM-like 16K mode, bank = (D3-D0 | E1.D1-D0 << 4) mirrored at $8000/$C000
 *   $5001: E1  D3 = 1: PRG inner mask $1F / CHR inner mask $FF; 0: PRG mask $0F + E1.D4, CHR mask $7F + E1.D4<<3
 *              PRG outer = E1.D1-D0 << 5 (8K units), CHR outer = E1.D1-D0 << 8 (1K units)
 *   $5007: E2  != 0: scrambled MMC3 registers: $8000 -> $C000, $8001 -> bank select (low 3 bits permuted
 *              0,6,3,7,5,2,4,1), $A000 -> bank data (once per select; in NROM mode only for CHR regs),
 *              $A001 -> mirroring; $C000-$FFFF unchanged.
 *   Reset: E0 = 0, E1 = $FF, E2 = 3 (scrambled), MMC3 IRQ on A12.
 *   The 16K mode is kept across later MMC3 writes (Mesen drops it on the next MMC3 bank write; the hardware
 *   treats E0.D7 as a mode bit, which the $A000 gating above suggests).
 * ====================================================================================================== */
static const uint8_t m217_lut[8] = { 0, 6, 3, 7, 5, 2, 4, 1 };
static void m217_sync(cart_t *c) {
    mmc3_state_t *s = &c->s.mmc3;
    uint8_t e0 = s->ext[0], e1 = s->ext[1];
    bool wide = e1 & 8;
    s->prg_and = wide ? 0x1F : 0x0F;
    s->prg_or  = (uint16_t)(((e1 << 5) & 0x60) | (wide ? 0 : (e1 & 0x10)));
    s->chr_and = wide ? 0xFF : 0x7F;
    s->chr_or  = (uint16_t)(((e1 << 8) & 0x300) | (wide ? 0 : ((e1 << 3) & 0x80)));
    mmc3_sync(c);
    if (e0 & 0x80) {
        uint32_t b = (uint32_t)(((e0 & 0x0F) | ((e1 << 4) & 0x30)) << 1);
        for (unsigned i = 0; i < 4; i++) cart_set_prg8k(c, i, (int32_t)(((b + (i & 1)) & s->prg_and) | s->prg_or));
    }
}
static void m217_init(cart_t *c) {
    mmc3_init(c);
    mmc3_state_t *s = &c->s.mmc3;
    s->variant = 0;   /* plain MMC3 whatever the submapper says */
    s->ext[0] = 0; s->ext[1] = 0xFF; s->ext[2] = 3; s->ext[3] = 0;
    m217_sync(c);
}
static void m217_write(cart_t *c, uint16_t a, uint8_t v) {
    mmc3_state_t *s = &c->s.mmc3;
    if (a < 0x8000) {
        switch (a) {
        case 0x5000: s->ext[0] = v; break;
        case 0x5001: s->ext[1] = v; break;
        case 0x5007: s->ext[2] = v; return;
        default: return;
        }
        m217_sync(c);
        return;
    }
    bool scr = s->ext[2] != 0;
    switch (a & 0xE001) {
    case 0x8000: mmc3_write(c, scr ? 0xC000 : 0x8000, v); break;
    case 0x8001:
        if (scr) { s->ext[3] = 1; mmc3_write(c, 0x8000, (uint8_t)((v & 0xC0) | m217_lut[v & 7])); }
        else mmc3_write(c, 0x8001, v);
        break;
    case 0xA000:
        if (scr) {
            if (s->ext[3] && (!(s->ext[0] & 0x80) || (s->bank_select & 7) < 6)) { s->ext[3] = 0; mmc3_write(c, 0x8001, v); }
        } else mmc3_write(c, 0xA000, v);
        break;
    case 0xA001: mmc3_write(c, scr ? 0xA000 : 0xA001, v); break;
    default: mmc3_write(c, a, v); return;   /* $C000-$FFFF: IRQ, no bank change */
    }
    m217_sync(c);
}
const mapper_desc_t mapper_217 = { 217, "BMC-255in1(MMC3)", MF_PPU_HOOK, m217_init, m217_write, NULL, mmc3_ppu_addr, NULL, NULL };

/* ======================================================================================================
 * 232  Camerica BF9096 / Quattro (Codemasters)
 *   $8000-$BFFF: D~[...B B...] 64K block; $C000-$FFFF: D~[.... ..PP] 16K page in the block.
 *   $8000 = block*4 + PP, $C000 = block*4 + 3. CHR-RAM 8K, mirroring hard-wired, no bus conflicts
 *   (BF9096 is a custom chip). Power-on: block 0, page 0.
 *   Submapper 1 (Aladdin Deck Enhancer): block bits swapped, block = D4 | D3 << 1 (as NES 2.0 / Mesen2).
 *   The lockout-defeat charge pump is irrelevant here.
 * ====================================================================================================== */
static void m232_sync(cart_t *c) {
    uint8_t blk = c->s.g.regs[0], pg = c->s.g.regs[1];
    cart_set_prg16k(c, 0, (blk << 2) | pg);
    cart_set_prg16k(c, 1, (blk << 2) | 3);
}
static void m232_init(cart_t *c) { c->s.g.regs[0] = 0; c->s.g.regs[1] = 0; cart_set_chr8k(c, 0); m232_sync(c); }
static void m232_write(cart_t *c, uint16_t a, uint8_t v) {
    if (a >= 0xC000) c->s.g.regs[1] = v & 3;
    else if (a >= 0x8000) c->s.g.regs[0] = (c->submapper == 1) ? (uint8_t)(((v >> 4) & 1) | ((v >> 2) & 2)) : (uint8_t)((v >> 3) & 3);
    else return;
    m232_sync(c);
}
const mapper_desc_t mapper_232 = { 232, "Camerica-BF9096", 0, m232_init, m232_write, NULL, NULL, NULL, NULL };

/* ======================================================================================================
 * 234  AVE Maxi 15 (see the firmware note at the top of the file)
 *   $FF80-$FF9F outer: D~[MOQq BBBb]  M = mirroring (0 V, 1 H), O = mode (0 CNROM, 1 NINA-03),
 *       Q/q = ROM pair select / disable, BBBb = block. Locked (ignores further updates) once any of D5-D0 is set.
 *   $FFC0-$FFDF lockout defeat: not needed for emulation (ignored).
 *   $FFE8-$FFF7 inner (never locked): D~[.cCC ...P]
 *   CNROM mode: 32K PRG = BBBb, 8K CHR = BBBbCC.  NINA-03 mode: 32K PRG = BBBP, 8K CHR = BBBcCC.
 *   Reads latch the ROM byte; writes latch too, with bus conflicts. All registers cleared on reset.
 *   Q/q are not used as extra bank bits (as in Mesen2): the known 512K PRG + 512K CHR dumps are fully covered
 *   by BBBb, so "ROMs 3+4" are already inside that range; the q "disable ROMs 3+4" open-bus case is not emulated.
 * ====================================================================================================== */
static void m234_sync(cart_t *c) {
    uint8_t r0 = c->s.g.regs[0], r1 = c->s.g.regs[1];
    if (r0 & 0x40) { cart_set_prg32k(c, (r0 & 0x0E) | (r1 & 1)); cart_set_chr8k(c, ((r0 << 2) & 0x38) | ((r1 >> 4) & 7)); }
    else           { cart_set_prg32k(c, r0 & 0x0F);              cart_set_chr8k(c, ((r0 << 2) & 0x3C) | ((r1 >> 4) & 3)); }
    cart_set_mirroring(c, (r0 & 0x80) ? MIRROR_H : MIRROR_V);
}
void FC_FASTCODE(m234_latch)(cart_t *c, uint16_t a, uint8_t v) {
    if (a >= 0xFF80 && a <= 0xFF9F) { if (c->s.g.regs[0] & 0x3F) return; c->s.g.regs[0] = v; }
    else if (a >= 0xFFE8 && a <= 0xFFF7) c->s.g.regs[1] = v & 0x71;
    else return;
    m234_sync(c);
}
static uint8_t FC_FASTCODE(m234_peek)(cart_t *c, uint16_t a, uint8_t open) {
#if FC_VIRTUAL_ROM
    (void)c; (void)a; return open;   /* ROM bytes are not readable from the core on rev D */
#else
    const uint8_t *p = c->prg_map[a >> 13];
    return (a >= 0x8000 && p) ? p[a & 0x1FFF] : open;
#endif
}
void FC_FASTCODE(m234_rom_read)(cart_t *c, uint16_t a) {
#if !FC_VIRTUAL_ROM
    if (a < 0xFF80 || a > 0xFFF7) return;
    const uint8_t *p = c->prg_map[a >> 13];
    if (p) m234_latch(c, a, p[a & 0x1FFF]);
#else
    (void)c; (void)a;
#endif
}
static uint8_t FC_FASTCODE(m234_read)(cart_t *c, uint16_t a, uint8_t open) {
    uint8_t v = m234_peek(c, a, open);
    if (a >= 0x8000) m234_latch(c, a, v);
    return v;
}
static void m234_init(cart_t *c) { c->s.g.regs[0] = 0; c->s.g.regs[1] = 0; cart_unmap_6000(c); m234_sync(c); }
static void m234_write(cart_t *c, uint16_t a, uint8_t v) { m234_latch(c, a, v); }   /* v already ANDed with ROM */
/* No MF_READ_LOW: there is nothing readable in $4020-$7FFF; read/peek are for the ROM-read hook only. */
const mapper_desc_t mapper_234 = { 234, "AVE-Maxi15", MF_BUS_CONFLICT, m234_init, m234_write, m234_read, NULL, NULL, m234_peek };

/* ======================================================================================================
 * 27  World Hero (unlicensed VRC4 clone), with UNL-CC-21 "Mi Hun Che" detected by ROM size
 *   nesdev: VRC4 with mask $F00F, register A0/A1 on CPU A0/A1 (like 23 submapper 1 / VRC4f):
 *   $8000 PRG0 (8K at $8000, or $C000 when $9002.D1 = 1), $A000 PRG1, $9000-$9001 mirroring
 *   (0 V, 1 H, 2 1scA, 3 1scB), $9002-$9003 D1 PRG swap mode, $B000-$E003 1K CHR banks with 9-bit numbers
 *   (even = low 4 bits, odd = high 5 bits, A1 = second bank of the pair), $F000/$F001 IRQ latch low/high
 *   nibble, $F002 IRQ control, $F003 ack. $E000-$FFFF fixed to the last bank, $C000 (or $8000) second last.
 *   The wiki leaves the IRQ style open (VRC vs. A12); like Mesen2 (and FCEUX's former dup of 23) the VRC4
 *   CPU-cycle IRQ is used: 8-bit up counter, prescaler 341/3 (scanline mode) or every M2 (cycle mode),
 *   reload from latch on overflow. Power-on: PRG 0/1, CHR 0-7. WRAM at $6000 if the header has any.
 *   CC-21 (FCEUX r2947+ maps it to 27): 32K PRG, 8K (or overdumped 16K) CHR. $8000 latches D0, $8001-$FFFF
 *   latch A0; bit 0 = 4K CHR bank at both $0000 and $1000 (8K bank with 16K CHR) and 1scA/1scB mirroring.
 *   Chosen when PRG is 32 KiB and CHR-ROM is 8 or 16 KiB (World Hero is far bigger).
 * ====================================================================================================== */
typedef struct {
    uint8_t prg[2], mode, mirroring;
    uint16_t chr[8];
    uint8_t irq_latch, irq_ctrl, irq_counter; int16_t prescaler;
    uint8_t cc21;
} m27_t;
_Static_assert(sizeof(m27_t) <= sizeof(((cart_t *)0)->s.raw), "m27 state");
static void m27_cc21_apply(cart_t *c, uint8_t l) {
    if (c->chr_size == 8192) { cart_set_chr4k(c, 0, l & 1); cart_set_chr4k(c, 1, l & 1); }
    else cart_set_chr8k(c, l & 1);
    cart_set_mirroring(c, (l & 1) ? MIRROR_1B : MIRROR_1A);
}
static void m27_sync(cart_t *c) {
    m27_t *s = (m27_t *)c->s.raw;
    if (s->mode & 2) { cart_set_prg8k(c, 0, -2); cart_set_prg8k(c, 2, s->prg[0]); }
    else { cart_set_prg8k(c, 0, s->prg[0]); cart_set_prg8k(c, 2, -2); }
    cart_set_prg8k(c, 1, s->prg[1]); cart_set_prg8k(c, 3, -1);
    for (unsigned i = 0; i < 8; i++) cart_set_chr1k(c, i, s->chr[i]);
    static const mirroring_t mm[4] = { MIRROR_V, MIRROR_H, MIRROR_1A, MIRROR_1B };
    cart_set_mirroring(c, mm[s->mirroring & 3]);
}
static void m27_init(cart_t *c) {
    m27_t *s = (m27_t *)c->s.raw;
    s->cc21 = c->prg_size == 32768 && !c->chr_is_ram && (c->chr_size == 8192 || c->chr_size == 16384);
    if (s->cc21) { cart_set_prg32k(c, 0); cart_set_chr8k(c, 0); cart_unmap_6000(c); if (c->chr_size == 8192) cart_set_chr4k(c, 1, 0); return; }
    s->prg[0] = 0; s->prg[1] = 1; s->mode = 0; s->mirroring = c->mirroring == MIRROR_H ? 1 : 0;
    for (unsigned i = 0; i < 8; i++) s->chr[i] = (uint16_t)i;
    s->irq_latch = s->irq_ctrl = s->irq_counter = 0; s->prescaler = 341;
    if (c->wram_size) cart_set_wram_6000(c, 0, true); else cart_unmap_6000(c);
    m27_sync(c);
}
static void m27_write(cart_t *c, uint16_t a, uint8_t v) {
    m27_t *s = (m27_t *)c->s.raw;
    if (a < 0x8000) return;
    if (s->cc21) { m27_cc21_apply(c, a == 0x8000 ? v : (uint8_t)a); return; }
    unsigned r = a & 3;
    switch (a & 0xF000) {
    case 0x8000: s->prg[0] = v & 0x1F; break;
    case 0xA000: s->prg[1] = v & 0x1F; break;
    case 0x9000: if (r < 2) s->mirroring = v & 3; else s->mode = v & 2; break;
    case 0xB000: case 0xC000: case 0xD000: case 0xE000: {
        unsigned i = (((a >> 12) - 0xBu) << 1) | (r >> 1);
        if (r & 1) s->chr[i] = (uint16_t)((s->chr[i] & 0x0F) | ((v & 0x1Fu) << 4));
        else       s->chr[i] = (uint16_t)((s->chr[i] & 0x1F0) | (v & 0x0Fu));
        break; }
    case 0xF000:
        switch (r) {
        case 0: s->irq_latch = (uint8_t)((s->irq_latch & 0xF0) | (v & 0x0F)); break;
        case 1: s->irq_latch = (uint8_t)((s->irq_latch & 0x0F) | (v << 4)); break;
        case 2: s->irq_ctrl = v & 7; cart_irq(c, false); if (v & 2) { s->irq_counter = s->irq_latch; s->prescaler = 341; } break;
        default: cart_irq(c, false); s->irq_ctrl = (uint8_t)((s->irq_ctrl & ~2) | ((s->irq_ctrl & 1) << 1)); break;
        }
        return;
    }
    m27_sync(c);
}
static void FC_FASTCODE(m27_cycle)(cart_t *c) {
    m27_t *s = (m27_t *)c->s.raw;
    if (!(s->irq_ctrl & 2)) return;
    bool clk = false;
    if (s->irq_ctrl & 4) clk = true;
    else { s->prescaler -= 3; if (s->prescaler <= 0) { s->prescaler += 341; clk = true; } }
    if (clk) { if (s->irq_counter == 0xFF) { s->irq_counter = s->irq_latch; cart_irq(c, true); } else s->irq_counter++; }
}
const mapper_desc_t mapper_027 = { 27, "VRC4(WorldHero)/CC-21", MF_CPU_CYCLE, m27_init, m27_write, NULL, NULL, m27_cycle, NULL };

/* ======================================================================================================
 * 521  DREAMTECH01 (Korean Igo)
 *   $5020 (mask $F030; $5030 is ignored): D~[.... BBBB] 16K PRG bank at $8000. $C000 fixed to the last 16K of the
 *   file (a separate chip, so the file may be a non-power-of-two size). 8K unbanked CHR-RAM, hard-wired mirroring.
 *   Power-on state undocumented: bank 0.
 * ====================================================================================================== */
static void m521_init(cart_t *c) { cart_set_prg16k(c, 0, 0); cart_set_prg16k(c, 1, -1); cart_set_chr8k(c, 0); cart_unmap_6000(c); }
static void m521_write(cart_t *c, uint16_t a, uint8_t v) { if ((a & 0xF030) == 0x5020) cart_set_prg16k(c, 0, v & 0x0F); }
const mapper_desc_t mapper_521 = { 521, "DREAMTECH01", 0, m521_init, m521_write, NULL, NULL, NULL, NULL };
