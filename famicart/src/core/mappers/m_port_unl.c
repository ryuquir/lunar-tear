/* Unlicensed boards: Sachen 8259A/B/C (141/138/139), Sachen SA-008-A / Tengen 800008 (148),
 * Bit Corp UNL-PCI556 (38), AGCI 50282 (144), NTDEC TC-112 (193), TXC 01-22000-400 (36), Racermate (168).
 * Tengen 800037 (158) lives in m064_rambo1.c because it shares the RAMBO-1 core.
 * Register maps checked against https://www.nesdev.org/wiki/INES_Mapper_NNN and .../Sachen_8259. */
#include "../mapper.h"
#include "../cartload.h"   /* FC_VIRTUAL_ROM */

/* ---- 141 / 138 / 139 Sachen 8259A / 8259B / 8259C ----------------------------------------------
 * $4100 (mask $C101): register select (D2-D0); $4101: data (D2-D0) to the selected register.
 * R0-R3: low 3 bits of the CHR bank for PPU $0000/$0800/$1000/$1800; R4: high 3 bits of all four;
 * R5: 32 KiB PRG bank; R6: unused; R7: D0 simple mode (all windows use R0, mirroring forced V),
 * D2-D1 mirroring 0 V, 1 H, 2 (0,1,1,1), 3 single-screen A. No PRG RAM, no bus conflicts.
 * CHR rewiring: the 6-bit window value r drives CHR A16-A11 (B, shift 0), A17-A12 (A, shift 1) or
 * A18-A13 (C, shift 2) with the low PPU address bits passing straight through, so the low address
 * bits "leak" in simple mode as on hardware. Power-on state is undocumented: all registers 0.
 * 8259D (137) behaves differently and is not implemented here. Q-Boy (8 KiB unbanked CHR-RAM, often
 * tagged 141) works too: CHR-RAM smaller than the bank range just wraps onto the single 8 KiB page. */
static void s8259_sync(cart_t *c, unsigned shift) {
    const uint8_t *r = c->s.g.regs;   /* regs[0..7] internal registers, regs[8] select */
    bool simple = r[7] & 1;
    cart_set_prg32k(c, r[5] & 7);
    for (unsigned j = 0; j < 8; j++) {
        unsigned w = simple ? 0 : (j >> 1);
        unsigned v = ((r[4] & 7u) << 3) | (r[w] & 7u);
        unsigned low = j & ((1u << (shift + 1)) - 1);    /* PPU A10 (+A11, +A12) pass through */
        cart_set_chr1k(c, j, (int32_t)((v << (shift + 1)) | low));
    }
    unsigned m = simple ? 0 : ((r[7] >> 1) & 3);
    switch (m) {
    case 0: cart_set_mirroring(c, MIRROR_V); break;
    case 1: cart_set_mirroring(c, MIRROR_H); break;
    case 2: cart_set_nt_ciram(c, 0, 0); cart_set_nt_ciram(c, 1, 1); cart_set_nt_ciram(c, 2, 1); cart_set_nt_ciram(c, 3, 1); break;
    default: cart_set_mirroring(c, MIRROR_1A); break;
    }
}
static unsigned s8259_shift(const cart_t *c) { return c->mapper_id == 138 ? 0 : c->mapper_id == 139 ? 2 : 1; }
static void s8259_init(cart_t *c) { cart_unmap_6000(c); s8259_sync(c, s8259_shift(c)); }
static void s8259_write(cart_t *c, uint16_t a, uint8_t v) {
    uint8_t *r = c->s.g.regs;
    switch (a & 0xC101) {
    case 0x4100: r[8] = v & 7; break;
    case 0x4101: r[r[8]] = v & 7; s8259_sync(c, s8259_shift(c)); break;
    }
}
const mapper_desc_t mapper_141 = { 141, "Sachen-8259A", 0, s8259_init, s8259_write, NULL, NULL, NULL, NULL };
const mapper_desc_t mapper_138 = { 138, "Sachen-8259B", 0, s8259_init, s8259_write, NULL, NULL, NULL, NULL };
const mapper_desc_t mapper_139 = { 139, "Sachen-8259C", 0, s8259_init, s8259_write, NULL, NULL, NULL, NULL };

/* ---- 148 Sachen SA-008-A / Tengen 800008 -------------------------------------------------------
 * $8000-$FFFF [.... PCCC]: P = 32 KiB PRG bank, CCC = 8 KiB CHR bank. Bus conflicts. Mirroring
 * hard-wired. (SA-008-A decodes with mask $E000 per nesdev; we accept the whole $8000-$FFFF range,
 * a superset that well-behaved software cannot tell apart.) */
static void m148_init(cart_t *c) { cart_set_prg32k(c, 0); cart_set_chr8k(c, 0); }
static void m148_write(cart_t *c, uint16_t a, uint8_t v) { if (a >= 0x8000) { cart_set_prg32k(c, (v >> 3) & 1); cart_set_chr8k(c, v & 7); } }
const mapper_desc_t mapper_148 = { 148, "Sachen-SA-008-A", MF_BUS_CONFLICT, m148_init, m148_write, NULL, NULL, NULL, NULL };

/* ---- 38 UNL-PCI556 (Bit Corp, Crime Busters) ---------------------------------------------------
 * $7000-$7FFF [.... CCPP]: CC = 8 KiB CHR, PP = 32 KiB PRG. No PRG RAM, no bus conflicts, mirroring
 * hard-wired V (header). nesdev notes $F000-$FFFF writes "will likely" also latch; not emulated since
 * software must not rely on it. */
static void m38_init(cart_t *c) { cart_set_prg32k(c, 0); cart_set_chr8k(c, 0); cart_unmap_6000(c); }
static void m38_write(cart_t *c, uint16_t a, uint8_t v) { if ((a & 0xF000) == 0x7000) { cart_set_prg32k(c, v & 3); cart_set_chr8k(c, (v >> 2) & 3); } }
const mapper_desc_t mapper_038 = { 38, "UNL-PCI556", 0, m38_init, m38_write, NULL, NULL, NULL, NULL };

/* ---- 144 AGCI 50282 (Death Race) ---------------------------------------------------------------
 * Color Dreams (11): $8000-$FFFF [CCCC ..PP]. A 300 ohm resistor on D0 means the ROM's D0 always wins
 * the bus conflict: effective = ROM[addr] & (written | 1). This happens on every write regardless of
 * the database bus-conflict flag, so it is applied here rather than via MF_BUS_CONFLICT. Under
 * FC_VIRTUAL_ROM (rev D) ROM bytes are not readable from the core, so the written value is used. */
static void m144_write(cart_t *c, uint16_t a, uint8_t v) {
    if (a < 0x8000) return;
#if !FC_VIRTUAL_ROM
    const uint8_t *p = c->prg_map[a >> 13];
    if (p) v = p[a & 0x1FFF] & (uint8_t)(v | 1);
#endif
    cart_set_prg32k(c, v & 3); cart_set_chr8k(c, v >> 4);
}
const mapper_desc_t mapper_144 = { 144, "AGCI-50282", 0, m148_init, m144_write, NULL, NULL, NULL, NULL };

/* ---- 193 NTDEC TC-112 (Fighting Hero, War in the Gulf) -----------------------------------------
 * $6000-$7FFF mask $E007 (no SRAM): $6000 4 KiB CHR at PPU $0000 (D7-D2 = 1K bank & ~3),
 * $6001 2 KiB CHR at $1000 (D7-D1), $6002 2 KiB CHR at $1800 (D7-D1), $6003 8 KiB PRG at $8000
 * (D3-D0), $A000/$C000/$E000 fixed to -3/-2/-1. $6004 D0: 0 V, 1 H (some boards hard-wire it; the
 * header mirroring is kept until $6004 is written). Power-on state undocumented: registers 0. */
static void m193_init(cart_t *c) {
    cart_unmap_6000(c);
    cart_set_prg8k(c, 0, 0); cart_set_prg8k(c, 1, -3); cart_set_prg8k(c, 2, -2); cart_set_prg8k(c, 3, -1);
    cart_set_chr8k(c, 0);
}
static void m193_write(cart_t *c, uint16_t a, uint8_t v) {
    if ((a & 0xE000) != 0x6000) return;
    switch (a & 7) {
    case 0: cart_set_chr4k(c, 0, v >> 2); break;
    case 1: cart_set_chr2k(c, 2, v >> 1); break;
    case 2: cart_set_chr2k(c, 3, v >> 1); break;
    case 3: cart_set_prg8k(c, 0, v & 0x0F); break;
    case 4: cart_set_mirroring(c, (v & 1) ? MIRROR_H : MIRROR_V); break;
    }
}
const mapper_desc_t mapper_193 = { 193, "NTDEC-TC-112", 0, m193_init, m193_write, NULL, NULL, NULL, NULL };

/* ---- 36 TXC 01-22000-400 (Strike Wolf, Policeman) ----------------------------------------------
 * ASIC 05-00002-010 (PRG): read $4100 (mask $E100) [xxRR xxxx] = RR, other bits open bus.
 * Write (mask $E103): $4100 RR = increment mode ? RR+1 : invert ? ~PP : PP; $4101 [...V ....] invert;
 * $4102 [..PP ....] PP; $4103 [...C ....] increment. Write $8000-$FFFF: RR -> PRG pins (32 KiB bank).
 * 74-series CHR: write mask $E200 [.... CCCC] 8 KiB CHR bank. Mirroring from the header.
 * The $4100 read has no side effect, so peek() is not needed. Power-on state undocumented: all 0. */
enum { TXC_RR, TXC_PP, TXC_INV, TXC_INC };
static void m36_init(cart_t *c) { cart_set_prg32k(c, 0); cart_set_chr8k(c, 0); }
static void m36_write(cart_t *c, uint16_t a, uint8_t v) {
    uint8_t *r = c->s.g.regs;
    if (a >= 0x8000) { cart_set_prg32k(c, r[TXC_RR] & 3); return; }
    if (a >= 0x6000) return;
    if ((a & 0xE200) == 0x4200) cart_set_chr8k(c, v & 0x0F);
    switch (a & 0xE103) {
    case 0x4100: r[TXC_RR] = (uint8_t)((r[TXC_INC] ? r[TXC_RR] + 1 : r[TXC_INV] ? ~r[TXC_PP] : r[TXC_PP]) & 3); break;
    case 0x4101: r[TXC_INV] = (v >> 4) & 1; break;
    case 0x4102: r[TXC_PP] = (v >> 4) & 3; break;
    case 0x4103: r[TXC_INC] = (v >> 4) & 1; break;
    }
}
static uint8_t FC_FASTCODE(m36_read)(cart_t *c, uint16_t a, uint8_t ob) {
    if ((a & 0xE100) == 0x4100) return (uint8_t)((ob & 0xCF) | ((c->s.g.regs[TXC_RR] & 3) << 4));
    return ob;
}
const mapper_desc_t mapper_036 = { 36, "TXC-01-22000-400", MF_READ_LOW, m36_init, m36_write, m36_read, NULL, NULL, NULL };

/* ---- 168 Racermate --------------------------------------------------------------------------------
 * $8000-$BFFF [PP.. CCCC]: PP = 16 KiB PRG at $8000 ($C000 fixed last), CCCC = 4 KiB CHR-RAM bank at
 * PPU $1000 ($0000 fixed to bank 0). 64 KiB CHR-RAM, mirroring hard-wired V.
 * $C000-$FFFF: D2 (= Z, the reworked boards; the original A7 wiring is not emulated) 1: IRQ acknowledged
 * and the M2 counter held at 0; 0: counter runs. /IRQ is asserted while the counter's 1024s bit is set
 * (so it self-acknowledges after another 1024 M2). A Z 1->0 transition clears the RAM-protect bit.
 * While protected, the battery-backed SRAM U2 (CHR banks 8-15, always battery-backed) reads open bus
 * (served here as $FF) and ignores writes; U1 (banks 0-7) is treated as the factory default (no
 * battery, always accessible). Power-on: counter running, protection set.
 * State: regs[0] bank reg, regs[1] Z, regs[2] protect, r16[0] counter. */
static uint8_t m168_openbus[1024];
static void m168_sync(cart_t *c) {
    uint8_t *r = c->s.g.regs;
    cart_set_prg16k(c, 0, r[0] >> 6); cart_set_prg16k(c, 1, -1);
    cart_set_chr4k(c, 0, 0);
    unsigned b = r[0] & 0x0F;
    if ((b & 8) && r[2]) for (unsigned i = 0; i < 4; i++) cart_set_chr1k_ptr(c, 4 + i, m168_openbus, false);
    else cart_set_chr4k(c, 1, (int32_t)b);
}
static void m168_init(cart_t *c) {
    for (unsigned i = 0; i < sizeof m168_openbus; i++) m168_openbus[i] = 0xFF;
    c->s.g.regs[2] = 1; m168_sync(c);
}
static void m168_write(cart_t *c, uint16_t a, uint8_t v) {
    uint8_t *r = c->s.g.regs;
    if (a < 0x8000) return;
    if (a < 0xC000) { r[0] = v; m168_sync(c); return; }
    uint8_t z = (v >> 2) & 1;
    if (r[1] && !z) { r[2] = 0; m168_sync(c); }
    r[1] = z;
    if (z) { c->s.g.r16[0] = 0; cart_irq(c, false); }
}
static void FC_FASTCODE(m168_cycle)(cart_t *c) {
    if (c->s.g.regs[1]) return;
    uint16_t n = (uint16_t)(c->s.g.r16[0] + 1);
    c->s.g.r16[0] = n;
    cart_irq(c, (n & 0x400) != 0);
}
const mapper_desc_t mapper_168 = { 168, "Racermate", MF_CPU_CYCLE, m168_init, m168_write, NULL, NULL, m168_cycle, NULL };
