/* MMC3 core, shared by MMC3-based boards (multicarts, PAL-ZZ, NES-QJ, TXC, Sachen ...).
 * Outer banks: set s.mmc3.prg_and/prg_or (8K units) and chr_and/chr_or (1K units), then mmc3_sync(). */
#pragma once
#include "../cart.h"
void mmc3_init(cart_t *c);                       /* power-on state (outer masks cleared) */
void mmc3_write(cart_t *c, uint16_t a, uint8_t v);/* $8000-$FFFF registers */
void mmc3_sync(cart_t *c);                       /* re-apply PRG/CHR/WRAM after changing the outer bank */
void mmc3_ppu_addr(cart_t *c, uint16_t a);       /* A12 IRQ clock (works with A12/A13 only, rev E U3) */
void mmc3_clock_irq(cart_t *c);
