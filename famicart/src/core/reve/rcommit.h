/* rev E, U1: decide which CPU reads really happened. U1 does not see M2 or R/W, only A0-A14, /ROMSEL and the write
 * strobe /WS. A cycle whose address stayed put for at least RC_MIN_DWELL, during which /ROMSEL never went low (so
 * A15 = 0) and /WS never went low (so it was not a write), was a read of that address. This is what U1 uses for
 * reads with side effects: PPU $2002/$2007 (VRAM pointer model), MMC5 $5204, N163 $4800, and the boot handshake.
 * Short dwells are the skew between address bits while the bus changes and are ignored. */
#pragma once
#include <stdint.h>
#include <stdbool.h>

typedef struct { uint16_t addr; uint32_t t0; uint8_t saw_romsel, saw_ws, valid; } rcommit_t;

static inline void rcommit_init(rcommit_t *r) { r->addr = 0xFFFF; r->t0 = 0; r->saw_romsel = r->saw_ws = 0; r->valid = 0; }
/* Call on every sample. a15 = A0-A14, now = free running time in the caller's units, min_dwell in the same units.
 * Returns true when the previous address is confirmed as a completed read; *out = that address (A15 = 0). */
static inline bool rcommit_sample(rcommit_t *r, uint16_t a15, bool romsel_low, bool ws_low, uint32_t now, uint32_t min_dwell, uint16_t *out) {
    bool done = false;
    if (a15 != r->addr) {
        if (r->valid && !r->saw_romsel && !r->saw_ws && (uint32_t)(now - r->t0) >= min_dwell) { *out = r->addr; done = true; }
        r->addr = a15; r->t0 = now; r->saw_romsel = 0; r->saw_ws = 0; r->valid = 1;
    }
    if (romsel_low) r->saw_romsel = 1;
    if (ws_low) r->saw_ws = 1;
    return done;
}
/* Which confirmed reads U1 cares about (cheap filter used before queueing). */
static inline bool rcommit_wanted(uint16_t a, bool mapper_side_effects) {
    if ((a & 0xE000) == 0x2000) return (a & 7) == 2 || (a & 7) == 7;
    if (a >= 0x4C4C && a <= 0x4C4E) return true;                       /* boot handshake */
    return mapper_side_effects && a >= 0x4020;
}
