/* Licensed Famicom/NES boards: Irem 74*161/161/21/138 (77), Bandai Oeka Kids (96), Jaleco JF-10 misdump (101),
 * NES-EVENT / Nintendo World Championships 1990 (105), Fukutake Study Box (186), Bandai Karaoke Studio (188),
 * Front Fareast Magic Card 1M/2M (6). Bandai Datach (157) lives in m016_bandai.c (it shares the LZ93D50 core).
 * Register maps checked against https://www.nesdev.org/wiki/INES_Mapper_NNN, .../NES-EVENT, .../Fukutake_Study_Box
 * and .../Super_Magic_Card. */
#include "../mapper.h"
#include "mmc1.h"
#include <string.h>

/* ---- 77 Irem 74*161/161/21/138 (Napoleon Senki) -----------------------------------------------------------
 * $8000-$FFFF [CCCC PPPP] (bus conflicts): PPPP = 32 KiB PRG bank, CCCC = 2 KiB CHR-ROM bank at PPU $0000.
 * A 74138 splits the PPU space into 2 KiB regions: $0000-$07FF CHR-ROM; $0800-$27FF the 8 KiB RAM (6 KiB of
 * pattern RAM at $0800-$1FFF plus the nametables at $2000-$27FF); $2800-$2FFF CIRAM (CIRAM A10 = PPU A10), so it
 * is a fixed four-screen arrangement. The two RAM nametables use c->extvram (allocated for four-screen headers),
 * with a static fallback for headers that do not say four-screen. Power-on register state is undocumented: 0. */
#define m77_chrram (cart_aux_ram())                  /* 6 KB CHR-RAM at $0800-$1FFF */
#define m77_ntram (cart_aux_ram() + 6 * 1024)       /* 2 KB nametable RAM (when the header is not four-screen) */
static void m77_write(cart_t *c, uint16_t a, uint8_t v) {
    if (a < 0x8000) return;
    cart_set_prg32k(c, v & 0x0F);
    cart_set_chr2k(c, 0, v >> 4);
}
static void m77_init(cart_t *c) {
    memset(m77_chrram, 0, 6 * 1024);
    for (unsigned i = 2; i < 8; i++) cart_set_chr1k_ptr(c, i, m77_chrram + (i - 2) * 1024, true);
    uint8_t *nt = c->extvram ? c->extvram : m77_ntram;
    cart_set_nt_ptr(c, 0, nt); cart_set_nt_ptr(c, 1, nt + 1024);
    cart_set_nt_ciram(c, 2, 0); cart_set_nt_ciram(c, 3, 1);
    cart_unmap_6000(c);
    m77_write(c, 0x8000, 0);
}
const mapper_desc_t mapper_077 = { 77, "Irem-74161/161/21/138", MF_BUS_CONFLICT, m77_init, m77_write, NULL, NULL, NULL, NULL };

/* ---- 96 Bandai Oeka Kids -----------------------------------------------------------------------------------
 * $8000-$FFFF [.... .CPP] (bus conflicts): PP = 32 KiB PRG bank, C = 16 KiB outer CHR-RAM bank (32 KiB CHR-RAM).
 * Inner bank: a 7474 latches PPU A9-A8 when the PPU address moves into $2xxx (A13=1, A12=0) from anywhere else,
 * i.e. on every nametable fetch (the attribute fetch that follows stays in $2xxx and does not re-latch; $3xxx
 * never latches; $2006 writes do). PPU $0000-$0FFF = outer*4 + latched value, $1000-$1FFF = outer*4 + 3 (Disch's
 * numbering; the hardware's NOR inversion is invisible to software). Mirroring hard-wired vertical (header).
 * No PRG-RAM, no IRQ. Power-on state undocumented: all 0. regs[0] = outer reg, [1] = latched CC, [2] = in-$2xxx. */
static void m96_sync(cart_t *c) {
    const uint8_t *r = c->s.g.regs;
    unsigned outer = ((r[0] >> 2) & 1u) * 4u;
    cart_set_prg32k(c, r[0] & 3);
    cart_set_chr4k(c, 0, (int32_t)(outer + r[1]));
    cart_set_chr4k(c, 1, (int32_t)(outer + 3));
}
static void m96_init(cart_t *c) { cart_unmap_6000(c); m96_sync(c); }
static void m96_write(cart_t *c, uint16_t a, uint8_t v) { if (a >= 0x8000) { c->s.g.regs[0] = v; m96_sync(c); } }
static void FC_FASTCODE(m96_ppu)(cart_t *c, uint16_t a) {
    uint8_t *r = c->s.g.regs;
    uint8_t in2 = (a & 0x3000) == 0x2000;
    if (in2 && !r[2]) {
        uint8_t cc = (uint8_t)((a >> 8) & 3);
        if (cc != r[1]) { r[1] = cc; cart_set_chr4k(c, 0, (int32_t)(((r[0] >> 2) & 1u) * 4u + cc)); }
    }
    r[2] = in2;
}
const mapper_desc_t mapper_096 = { 96, "Bandai-OekaKids", MF_BUS_CONFLICT | MF_PPU_HOOK, m96_init, m96_write, NULL, m96_ppu, NULL, NULL };

/* ---- 101 Jaleco JF-10 misdump (Urusei Yatsura - Lum no Wedding Bell) ---------------------------------------
 * $6000-$7FFF [CCCC CCHL]: 8 KiB CHR-ROM bank, bits in order (J87 with the bits un-swapped; C bits only for
 * oversize images). NROM-style fixed PRG, mirroring hard-wired, no bus conflicts, no PRG-RAM. */
static void m101_init(cart_t *c) { cart_set_prg32k(c, 0); cart_set_chr8k(c, 0); cart_unmap_6000(c); }
static void m101_write(cart_t *c, uint16_t a, uint8_t v) { if (a >= 0x6000 && a < 0x8000) cart_set_chr8k(c, v); }
const mapper_desc_t mapper_101 = { 101, "Jaleco-JF-10(bad)", MF_WRITE_6000, m101_init, m101_write, NULL, NULL, NULL, NULL };

/* ---- 105 NES-EVENT (Nintendo World Championships 1990) -----------------------------------------------------
 * MMC1 with two 128 KiB PRG chips, 8 KiB unbanked CHR-RAM, 8 KiB PRG-RAM (MMC1 $E000 bit 4 disables it) and a
 * 30-bit M2 up-counter. MMC1 $A000 (CHR reg 0) is rewired: [...I OAA.].
 *  - I (bit 4): 1 = timer held at 0 and the IRQ acknowledged; 0 = count every M2.
 *  - Lock: after reset the first 32 KiB of chip 0 is mapped regardless of the registers until I goes 0 -> 1
 *    (the board latches the first rising edge of the I line; the MMC1 power-on value 0 counts as the low level).
 *  - O (bit 3) = 0: chip 0, AA = 32 KiB bank. O = 1: chip 1 with MMC1 PRG banking from $E000 (B = bits 2-0 of
 *    the 16 KiB bank, 8 banks in 128 KiB) and MMC1 $8000 bits P (3) / S (2): P=0 32 KiB, P=1 S=0 {first}/B,
 *    P=1 S=1 B/{last} of chip 1.
 *  - IRQ when the counter reaches $20000000 | DIP << 25 (DIP = switches D C B A, closed = 1). The tournament
 *    setting closed only C (DIP = 4): $28000000 M2 cycles = 374.96 s on NTSC, the familiar 6:14 timer.
 * Not emulated: MMC1 PRG A14 also reaching chip 0 (16+16 KiB layouts of chip 0 in O=0 / before unlocking), and
 * $A000 bit 0 / $C000, which only drive CHR lines the board does not use. */
#ifndef NWC_DIP
#define NWC_DIP 4u   /* tournament setting: only switch C closed -> 6:14 */
#endif
typedef struct { mmc1_state_t m; uint8_t lock; uint8_t last_i; uint32_t counter; } nwc_state_t;
_Static_assert(sizeof(nwc_state_t) <= sizeof(((cart_t *)0)->s.raw), "nwc state too large");
static void nwc_sync(cart_t *c) {
    nwc_state_t *s = (nwc_state_t *)c->s.raw;
    uint8_t r = s->m.chr0, i = (r >> 4) & 1;
    if (s->lock == 0 && !i) s->lock = 1;
    else if (s->lock == 1 && i) s->lock = 2;
    if (i) { s->counter = 0; cart_irq(c, false); }
    s->last_i = i;
    if (s->lock < 2) cart_set_prg32k(c, 0);
    else if (!(r & 0x08)) cart_set_prg32k(c, (r >> 1) & 3);
    else {
        uint8_t b = s->m.prg & 7;
        switch ((s->m.ctrl >> 2) & 3) {
        case 0: case 1: cart_set_prg32k(c, 4 + (b >> 1)); break;
        case 2: cart_set_prg16k(c, 0, 8); cart_set_prg16k(c, 1, 8 + b); break;
        default: cart_set_prg16k(c, 0, 8 + b); cart_set_prg16k(c, 1, 15); break;
        }
    }
    cart_set_chr8k(c, 0);   /* CHR-RAM is not banked */
    /* WRAM enable + mirroring were applied by mmc1_sync() */
}
static void nwc_init(cart_t *c) {
    nwc_state_t *s = (nwc_state_t *)c->s.raw;
    mmc1_init(c);
    s->lock = 0; s->counter = 0; s->last_i = 0;
    nwc_sync(c);
}
static void nwc_write(cart_t *c, uint16_t a, uint8_t v) { if (a >= 0x8000) { mmc1_write(c, a, v); nwc_sync(c); } }
static void FC_FASTCODE(nwc_cycle)(cart_t *c) {
    nwc_state_t *s = (nwc_state_t *)c->s.raw;
    if (s->last_i) return;
    s->counter = (s->counter + 1) & 0x3FFFFFFFu;
    if (s->counter == (0x20000000u | (NWC_DIP << 25))) cart_irq(c, true);
}
const mapper_desc_t mapper_105 = { 105, "NES-EVENT", MF_CPU_CYCLE, nwc_init, nwc_write, NULL, NULL, nwc_cycle, NULL };

/* ---- 186 Fukutake Study Box (BIOS) -------------------------------------------------------------------------
 * $4200 W [BB.. ..AA]: AA = 4 KiB RAM-A page at $5000-$5FFF, BB = 8 KiB RAM-B page at $6000-$7FFF.
 * $4201 W [.... PPPP]: 16 KiB PRG bank at $8000-$BFFF; $C000-$FFFF fixed to bank 0.
 * $4400-$4FFF: RAM-A page 0 (offset $400-$FFF; its first 1 KiB is only reachable through $5000).
 * $4202 W: tape drive control (ignored). Reads $4200 data / $4201 tape status / $4202 drive status: the tape
 * drive and its decoder are not emulated, so they read "nothing": $4200 = $00, $4201 = $80 (decoder disabled),
 * $4202 = $00 (not ready), and the tape IRQ never fires. CHR: 8 KiB CHR-RAM; nametables: four-screen.
 * RAM: nesdev gives 16 KiB RAM-A + 32 KiB RAM-B, but the core caps WRAM at 32 KiB, so c->wram is split in two
 * halves: low half = RAM-A, high half = RAM-B (16 KiB of RAM-B with a full 32 KiB WRAM: BB bit 7 is lost).
 * Power-on state undocumented: all 0. NOTE for rev E: U1's low_window() must cover $4200-$5FFF for these reads. */
static uint8_t *sbox_ram_a(cart_t *c, uint16_t a) {
    uint32_t half = c->wram_size / 2;
    if (half < 4096) return NULL;
    uint32_t page = (a >= 0x5000) ? (c->s.g.regs[0] & 3u) % (half / 4096) : 0;
    return c->wram + page * 4096 + (a & 0x0FFF);
}
static void sbox_sync(cart_t *c) {
    const uint8_t *r = c->s.g.regs;
    cart_set_prg16k(c, 0, r[1] & 0x0F);
    cart_set_prg16k(c, 1, 0);
    uint32_t half = c->wram_size / 2, pages = half / 8192;
    if (pages) cart_set_wram_6000(c, pages + ((r[0] >> 6) & 3u) % pages, true); else cart_unmap_6000(c);
}
static void sbox_init(cart_t *c) { cart_set_mirroring(c, MIRROR_4); sbox_sync(c); }
static void sbox_write(cart_t *c, uint16_t a, uint8_t v) {
    if (a == 0x4200) { c->s.g.regs[0] = v; sbox_sync(c); }
    else if (a == 0x4201) { c->s.g.regs[1] = v; sbox_sync(c); }
    else if (a >= 0x4400 && a < 0x6000) { uint8_t *p = sbox_ram_a(c, a); if (p) *p = v; }
}
static uint8_t FC_FASTCODE(sbox_read)(cart_t *c, uint16_t a, uint8_t open) {
    switch (a) { case 0x4200: return 0x00; case 0x4201: return 0x80; case 0x4202: return 0x00; default: break; }
    if (a >= 0x4400 && a < 0x6000) { uint8_t *p = sbox_ram_a(c, a); return p ? *p : open; }
    return open;
}
const mapper_desc_t mapper_186 = { 186, "Fukutake-StudyBox", MF_READ_LOW, sbox_init, sbox_write, sbox_read, NULL, NULL, NULL };

/* ---- 188 Bandai Karaoke Studio -----------------------------------------------------------------------------
 * $8000-$FFFF [.LXR BBBB] (bus conflicts): R = 1 internal ROM / 0 expansion ROM, BBBB = 16 KiB bank at $8000,
 * X = CIRAM A10 0: PPU A10 (vertical) 1: PPU A11 (horizontal), L = unused latch. $C000-$FFFF = last internal
 * bank. 256 KiB dumps are 128 KiB internal + 128 KiB expansion; with no expansion image selecting the expansion
 * ROM leaves $8000-$BFFF open bus (nesdev recommends correct open bus; the game fingerprints the slot).
 * $6000-$7FFF R [.... .MBA]: A/B buttons (0 = pressed), M = 1-bit microphone ADC; there is no microphone, so the
 * buttons read released (1), the microphone silent (0), other bits open bus. 8 KiB CHR-RAM. Power-on: 0. */
static void m188_sync(cart_t *c) {
    uint8_t v = c->s.g.regs[0];
    uint32_t n16 = c->prg_pages / 2, internal = n16 > 8 ? 8 : n16;
    if (!internal) internal = 1;
    cart_set_prg16k(c, 1, (int32_t)internal - 1);
    if (v & 0x10) cart_set_prg16k(c, 0, (int32_t)((v & 0x0Fu) % internal));
    else if (n16 > internal) cart_set_prg16k(c, 0, (int32_t)(internal + (v & 0x0Fu) % (n16 - internal)));
    else { c->prg_map[4] = c->prg_map[5] = NULL; c->prg_wmap[4] = c->prg_wmap[5] = NULL; c->tables_dirty = 1; }
    cart_set_mirroring(c, (v & 0x20) ? MIRROR_H : MIRROR_V);
}
static void m188_init(cart_t *c) { cart_unmap_6000(c); c->s.g.regs[0] = 0; m188_sync(c); }
static void m188_write(cart_t *c, uint16_t a, uint8_t v) { if (a >= 0x8000) { c->s.g.regs[0] = v; m188_sync(c); } }
static uint8_t FC_FASTCODE(m188_read)(cart_t *c, uint16_t a, uint8_t open) {
    (void)c;
    if (a >= 0x6000 && a < 0x8000) return (uint8_t)((open & 0xF8) | 0x03);
    return open;
}
const mapper_desc_t mapper_188 = { 188, "Bandai-Karaoke", MF_BUS_CONFLICT | MF_READ_LOW, m188_init, m188_write, m188_read, NULL, NULL, NULL };

/* ---- 6 Front Fareast Magic Card 1M/2M (FFE F4xxx), Play mode of the Super Magic Card ----------------------
 * $42FC-$42FF (A1 A0 in the address, data [MMMS ....]): A1 = 1 PRG write-protected + latch enabled (0: PRG
 *   writable, latch off); A0 = 0 one-screen (S = page), A0 = 1 two-screen (S = 0 vertical, 1 horizontal);
 *   MMM = latch banking mode. Power-on value $42FF = sub<<5 | (V ? 0 : $10).
 * $8000-$FFFF latch (no bus conflicts) per mode: 0 UNROM [.....PPP] 16K at $8000, bank 7 at $C000;
 *   1 UN1ROM+CHRSW [..PPPPCC] 16K/fixed 7 + 8K CHR; 2 UOROM [....PPPP] 16K/fixed 15; 3 reverse UOROM [..CCPPPP]
 *   fixed 15 at $8000, 16K at $C000, 8K CHR; 4 GNROM [..PP..CC] 32K + 8K CHR; 5 CNROM-256 [......CC];
 *   6 CNROM-128 [.......C]; 7 NROM-256 (modes 4-7: 32K bank 3 where fixed, CHR memory write-protected).
 * $4500 [.PWWI.NK] (power-on $42): WW = 8 KiB WRAM bank at $6000 (32 KiB), I = IRQ clock 0 M2 rise / 1 PA12 rise
 *   (unfiltered), N = 1 nametables from CIRAM / 0 from CHR via $4518-$451B, K = 1 1 KiB CHR mode via $4510-$4517.
 * IRQ: $4501 W acknowledge + stop; $4502 / $4503 W counter low / high byte and acknowledge, $4503 also starts
 *   counting; the 16-bit counter counts up and asserts /IRQ when it wraps $FFFF -> $0000.
 * Not emulated: GUI mode and its BIOS ($4500 bit 6), writes into PRG memory while it is not write-protected
 *   (the image lives in ROM here), the 2M/4M modes ($43FC-$43FF, $4504-$4507), MMC4 mode, the $5000-$5FFF scratch
 *   RAM and the parallel/floppy ports, state readback ($4500/$4501 reads). NES 1.0 files (submapper 0 here) are
 *   treated as submapper 1, as nesdev specifies; the Doctor-header trainer is up to the loader.
 * regs: [0] latch [1] $42Fx mode/A0/A1/S packed [2] $4500 [3] irq enabled [4] last A12, [8..19] $4510-$451B.
 * r16[0] = IRQ counter. */
static void ffe_sync(cart_t *c) {
    const uint8_t *r = c->s.g.regs;
    uint8_t L = r[0], mode = r[1] >> 5, mtype = r[1] & 1, sset = (r[1] >> 4) & 1;
    bool chr_wp = mode >= 4;
    uint8_t chr8 = 0;
    switch (mode) {
    case 0: cart_set_prg16k(c, 0, L & 7);  cart_set_prg16k(c, 1, 7);  break;
    case 1: cart_set_prg16k(c, 0, (L >> 2) & 15); cart_set_prg16k(c, 1, 7); chr8 = L & 3; break;
    case 2: cart_set_prg16k(c, 0, L & 15); cart_set_prg16k(c, 1, 15); break;
    case 3: cart_set_prg16k(c, 0, 15); cart_set_prg16k(c, 1, L & 15); chr8 = (L >> 4) & 3; break;
    case 4: cart_set_prg32k(c, (L >> 4) & 3); chr8 = L & 3; break;
    case 5: cart_set_prg32k(c, 3); chr8 = L & 3; break;
    case 6: cart_set_prg32k(c, 3); chr8 = L & 1; break;
    default: cart_set_prg32k(c, 3); break;
    }
    if (r[2] & 0x01) for (unsigned i = 0; i < 8; i++) cart_set_chr1k(c, i, r[8 + i]);
    else cart_set_chr8k(c, chr8);
    if (chr_wp) { c->chr_wmask = 0; c->tables_dirty = 1; }
    if (r[2] & 0x02) {
        if (mtype) cart_set_mirroring(c, sset ? MIRROR_H : MIRROR_V);
        else cart_set_mirroring(c, sset ? MIRROR_1B : MIRROR_1A);
    } else for (unsigned i = 0; i < 4; i++) cart_set_nt_chr1k(c, i, r[16 + i]);
    if (c->wram_size) cart_set_wram_6000(c, (r[2] >> 4) & 3, true);
}
static void ffe_init(cart_t *c) {
    uint8_t *r = c->s.g.regs;
    uint8_t sub = c->submapper ? (c->submapper & 7) : 1;
    r[0] = 0;
    r[1] = (uint8_t)((sub << 5) | (c->mirroring == MIRROR_V ? 0x00 : 0x10) | 0x02 /*A1*/ | 0x01 /*A0*/);
    r[2] = 0x42; r[3] = 0; r[4] = 0; c->s.g.r16[0] = 0;
    ffe_sync(c);
}
static void ffe_write(cart_t *c, uint16_t a, uint8_t v) {
    uint8_t *r = c->s.g.regs;
    if (a >= 0x8000) { if (r[1] & 0x02) { r[0] = v; ffe_sync(c); } return; }
    if (a >= 0x42FC && a <= 0x42FF) { r[1] = (uint8_t)((v & 0xF0) | (a & 3)); ffe_sync(c); return; }
    switch (a) {
    case 0x4500: r[2] = v; ffe_sync(c); break;
    case 0x4501: r[3] = 0; cart_irq(c, false); break;
    case 0x4502: c->s.g.r16[0] = (uint16_t)((c->s.g.r16[0] & 0xFF00) | v); cart_irq(c, false); break;
    case 0x4503: c->s.g.r16[0] = (uint16_t)((c->s.g.r16[0] & 0x00FF) | (v << 8)); r[3] = 1; cart_irq(c, false); break;
    default:
        if (a >= 0x4510 && a <= 0x451B) { r[8 + (a - 0x4510)] = v; ffe_sync(c); }
        break;
    }
}
static void FC_FASTCODE(ffe_clock)(cart_t *c) { if (++c->s.g.r16[0] == 0) cart_irq(c, true); }
static void FC_FASTCODE(ffe_cycle)(cart_t *c) { const uint8_t *r = c->s.g.regs; if (r[3] && !(r[2] & 0x08)) ffe_clock(c); }
static void FC_FASTCODE(ffe_ppu)(cart_t *c, uint16_t a) {
    uint8_t *r = c->s.g.regs, a12 = (a >> 12) & 1;
    if (a12 && !r[4] && r[3] && (r[2] & 0x08)) ffe_clock(c);
    r[4] = a12;
}
const mapper_desc_t mapper_006 = { 6, "FFE-F4xxx", MF_CPU_CYCLE | MF_PPU_HOOK, ffe_init, ffe_write, NULL, ffe_ppu, ffe_cycle, NULL };
