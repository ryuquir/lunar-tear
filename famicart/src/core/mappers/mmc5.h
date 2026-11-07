/* MMC5 entry points used by the rev E MCUs besides the generic mapper hooks. */
#pragma once
#include "../cart.h"
void mmc5_scanline(cart_t *c);               /* new scanline detected */
void mmc5_frame_end(cart_t *c);              /* PPU stopped reading: out of frame */
bool mmc5_a13_read(cart_t *c, bool a13);     /* U3: one PPU read with its A13 level; true at a new scanline */
