/* Tengen RAMBO-1 (64) and Tengen 800037 (158, RAMBO-1 with TxSROM-style nametable select;
 * https://www.nesdev.org/wiki/INES_Mapper_158).
 * Behaviour taken from furrtek's gate-level trace of the chip (https://github.com/furrtek/SiliconRE/tree/master/Misc/RAMBO-1,
 * RAMBO-1_schematics.pdf, GPL-2.0; "p<n> CELL" below = page and cell name), https://www.nesdev.org/wiki/RAMBO-1 and the
 * IRQ timings James measured on a cartridge (https://forums.nesdev.org/viewtopic.php?t=10439, 2013).
 * docs/03_mapper_coverage.md lists what was confirmed, what changed and what is still open. */
#include "../mapper.h"
#define RB_A12_LOW 16u   /* p3 J38 -> ... -> J41, 16 flip-flops on M2 fall: the filter is full when A12 was low at the last 16 */
static void rb_sync(cart_t *c) {
    rambo1_state_t *s = &c->s.rambo1;
    uint8_t m = (s->bank & 0x80) ? 4 : 0, b[8];
    if (s->bank & 0x20) { for (unsigned i = 0; i < 2; i++) { b[(m + i * 2) & 7] = s->chr[i]; b[(m + i * 2 + 1) & 7] = s->chr[6 + i]; } }
    else for (unsigned i = 0; i < 2; i++) { b[(m + i * 2) & 7] = (uint8_t)(s->chr[i] & ~1); b[(m + i * 2 + 1) & 7] = (uint8_t)(s->chr[i] | 1); }
    for (unsigned i = 0; i < 4; i++) b[((m ^ 4) + i) & 7] = s->chr[2 + i];
    for (unsigned i = 0; i < 8; i++) cart_set_chr1k(c, i, b[i]);
    /* P ($8000 bit 6) swaps $8000 and $C000 only. p5: F23 = P xor CPU A14 picks R6 or RF (MUX21 B28 D16 C27 B26 C28B
     * B31) when CPU A13 = 0; CPU A13 = 1 takes R7 OR CPU A14 (OR A38 E32 A26 A25 E37 A40), so $A000 is always R7 and
     * $E000 the last bank. */
    bool p = (s->bank & 0x40) != 0;
    cart_set_prg8k(c, 0, s->prg[p ? 2 : 0]);
    cart_set_prg8k(c, 1, s->prg[1]);
    cart_set_prg8k(c, 2, s->prg[p ? 0 : 2]);
    cart_set_prg8k(c, 3, -1);
    /* 158 (Tengen 800037): CHR A17 drives CIRAM A10 like TxSROM; a nametable fetch (PPU A12 = 0) uses the
     * bank that the current CHR mode maps at PPU $0000 + n*$400. $A000 mirroring is not connected. */
    if (c->mapper_id == 158) for (unsigned i = 0; i < 4; i++) cart_set_nt_ciram(c, i, b[i] >> 7);
    else cart_set_mirroring(c, s->mirroring ? MIRROR_H : MIRROR_V);
}
static void rb_init(cart_t *c) { rambo1_state_t *s = &c->s.rambo1; s->bank = 0; for (int i = 0; i < 8; i++) s->chr[i] = (uint8_t)i; s->prg[0] = 0; s->prg[1] = 1; s->prg[2] = 2; s->mirroring = 0; s->irq_enable = 0; s->a12_hi = 1; rb_sync(c); }
/* IRQ counter (p3). The counter cells clock when the output of the H37 mux rises. In scanline mode that output is
 * H41./Q = NOT(A12 filter full), resampled at M2 rise; in CPU mode it is the /4 prescaler G52. (The trace does not show
 * which edge the cells use; this is the one that gives /IRQ 1-2 CPU cycles after the A12 rise, as measured.) */
static void rb_write(cart_t *c, uint16_t a, uint8_t v) {
    rambo1_state_t *s = &c->s.rambo1; if (a < 0x8000) return;
    switch (a & 0xE001) {
    case 0x8000: s->bank = v; break;
    case 0x8001: { unsigned r = s->bank & 0x0F; if (r < 6) s->chr[r] = v; else if (r == 6 || r == 7) s->prg[r - 6] = v; else if (r == 8 || r == 9) s->chr[6 + (r - 8)] = v; else if (r == 0xF) s->prg[2] = v; } break;
    case 0xA000: s->mirroring = v & 1; break;
    case 0xC000: s->irq_latch = v; return;
    /* p3: /WR_C001 clears the counter cells (M47 -> CLR: count $FF), sets R2, clears R4, P4 and the prescaler (H40,
     * G52), and F30 takes D0 as the mode at its end. R4 takes R2 when the mux output falls and the next clock loads the
     * latch, so the load is the 1st clock after the write if the output is high when the write ends and the 2nd if it
     * is low (the 1st takes $FF to $FE). Scanline mode: high while the filter is not full (its filling sets R4), so the
     * IRQ comes at the L+1th or L+2th qualified A12 rise. Mode switch at the end of the write: to CPU mode from a high
     * output is a falling edge (load at the 1st prescaler clock); from CPU mode to a high H41./Q a rising one (a clock
     * of $FF, which changes nothing visible). CPU mode to CPU mode: the reset prescaler keeps the output low; clocks at
     * the 2nd M2 after the write ($FF -> $FE), the 6th (load) and every 4th after. A zero reached just before is dropped
     * (the count is $FF when G49 samples it); an IRQ already raised stays raised (G50 is not reset). */
    case 0xC001: {
        bool pend = !s->irq_mode && s->irq_next;   /* qualified A12 rise in this cycle: H41./Q was still low at its M2 rise */
        bool h41 = !pend && (s->a12_hi || (uint32_t)(c->cpu_cycles - s->a12_low_since) < RB_A12_LOW);
        s->irq_reload = (h41 && !(s->irq_mode & v & 1)) ? 1 : 2;
        s->irq_mode = v & 1; s->irq_next = (v & 1) ? 2 : pend; s->irq_counter = 0xFF; s->irq_due = 0;
        return;
    }
    case 0xE000: s->irq_enable = 0; cart_irq(c, false); return;   /* p3 E38 holds the IRQ flip-flop G50 clear */
    case 0xE001: s->irq_enable = 1; return;                        /* enable only, no acknowledge */
    }
    rb_sync(c);
}
/* One counter clock: the cells load the latch, as written, when the count is 0 or the $C001 handshake is due
 * (/LD = NOR(P2, R4) via R1, R3) and count down otherwise. G49 samples P2 (count = 0) at every M2 fall and G50 sets on
 * its rising edge, so only a clock that takes a non-zero count to 0 raises the IRQ (latch 0: one IRQ, not one per clock). */
static bool FC_FASTCODE(rb_clock)(rambo1_state_t *s) {
    uint8_t was = s->irq_counter;
    s->irq_counter = (was == 0 || s->irq_reload == 1) ? s->irq_latch : (uint8_t)(was - 1);
    if (s->irq_reload) s->irq_reload--;
    return was != 0 && s->irq_counter == 0;
}
/* A12 filter (runs in both modes). The first M2 fall that sees A12 high after 16 low ones empties the filter, H41 raises
 * the mux output at the next M2 rise (the next cpu_cycle()) and that clocks the counter in scanline mode. */
static void FC_FASTCODE(rb_ppu_addr)(cart_t *c, uint16_t a) {
    rambo1_state_t *s = &c->s.rambo1;
    if (!(a & 0x1000)) { if (s->a12_hi) { s->a12_hi = 0; s->a12_low_since = c->cpu_cycles; } return; }
    if (s->a12_hi) return;
    s->a12_hi = 1;
    if (!s->irq_mode && (uint32_t)(c->cpu_cycles - s->a12_low_since) >= RB_A12_LOW) s->irq_next = 1;
}
/* cpu_cycle() = the M2 fall that ends the last cycle, then the rise of this one. irq_due: a clock took the count to 0 at
 * the last rise, so G49 pulls /IRQ low at that fall unless $E000 has disabled it (E38 holds G50 clear): /IRQ 1-2 CPU
 * cycles after the A12 rise in scanline mode, 1/2 cycle after the clock in CPU mode. irq_next: rises until the next
 * clock (CPU mode: the /4 prescaler; scanline mode: 1 after a qualified A12 rise, else 0). */
static void FC_FASTCODE(rb_cycle)(cart_t *c) {
    rambo1_state_t *s = &c->s.rambo1;
    if (s->irq_due) { s->irq_due = 0; if (s->irq_enable) cart_irq(c, true); }
    if (s->irq_next && --s->irq_next == 0) { if (s->irq_mode) s->irq_next = 4; s->irq_due = rb_clock(s); }
}
const mapper_desc_t mapper_064 = { 64, "Tengen-RAMBO-1", MF_PPU_HOOK | MF_CPU_CYCLE, rb_init, rb_write, NULL, rb_ppu_addr, rb_cycle, NULL };
const mapper_desc_t mapper_158 = { 158, "Tengen-800037", MF_PPU_HOOK | MF_CPU_CYCLE, rb_init, rb_write, NULL, rb_ppu_addr, rb_cycle, NULL };
