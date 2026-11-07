/* rev E: rebuild the PPU's VRAM address register from the CPU side. The PPU /WR line is not wired to the cartridge,
 * so U1 follows $2000 (increment), $2002 reads (write toggle), $2005/$2006 (t/v) and $2007 accesses and tells U2
 * which VRAM byte each $2007 write stores (CHR-RAM, cartridge nametables, MMC5 ExRAM, U2's CIRAM shadow).
 * Rendering-time $2007 accesses (which glitch v on the real PPU) are not modelled; games set $2006 again before
 * uploading, so the model re-syncs on every upload. */
#pragma once
#include <stdint.h>
#include <stdbool.h>

typedef struct { uint16_t v, t; uint8_t w, inc32; } ppu_track_t;

static inline void ppu_track_reset(ppu_track_t *p) { p->v = p->t = 0; p->w = 0; p->inc32 = 0; }

/* CPU write to $2000-$3FFF (any mirror). Returns true for a $2007 write and sets *vaddr (14-bit). */
static inline bool ppu_track_write(ppu_track_t *p, uint16_t a, uint8_t d, uint16_t *vaddr) {
    switch (a & 7) {
    case 0: p->t = (uint16_t)((p->t & ~0x0C00u) | ((d & 3u) << 10)); p->inc32 = (d >> 2) & 1; break;
    case 5: if (!p->w) p->t = (uint16_t)((p->t & ~0x001Fu) | (d >> 3));
            else p->t = (uint16_t)((p->t & ~0x73E0u) | ((d & 7u) << 12) | ((d & 0xF8u) << 2));
            p->w ^= 1; break;
    case 6: if (!p->w) p->t = (uint16_t)((p->t & 0x00FFu) | ((d & 0x3Fu) << 8));
            else { p->t = (uint16_t)((p->t & 0xFF00u) | d); p->v = p->t; }
            p->w ^= 1; break;
    case 7: *vaddr = p->v & 0x3FFF; p->v = (uint16_t)((p->v + (p->inc32 ? 32 : 1)) & 0x7FFF); return true;
    default: break;
    }
    return false;
}
/* CPU read of $2000-$3FFF that really happened (see rcommit.h). */
static inline void ppu_track_read(ppu_track_t *p, uint16_t a) {
    if ((a & 7) == 2) p->w = 0;
    else if ((a & 7) == 7) p->v = (uint16_t)((p->v + (p->inc32 ? 32 : 1)) & 0x7FFF);
}
