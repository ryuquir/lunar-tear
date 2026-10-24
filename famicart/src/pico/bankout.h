/* rev D, U1: turn the cart's prg_map/prg_wmap tables into PRG flash / F-RAM bank lines + WRAM /CE. */
#pragma once
#include "../core/cart.h"
void bankout_init(void);                                  /* GPIO setup: boot bank on the lines, WRAM off */
void bankout_set_cart(cart_t *c, uint32_t prg_base_bank);  /* prg_base_bank: 8 KB bank index of the game's PRG in the flash */
void bankout_update(cart_t *c);                           /* re-encode the tables (call when c->tables_dirty) */
void bankout_boot(void);                                  /* every window -> boot bank, WRAM off */
void bankout_go(bool live);                               /* live: use the cart tables; false: boot state */
void bankout_core1(void);                                 /* never returns: the fast window -> bank loop */
void bankout_set_raw(uint32_t bank, bool wram_sel);       /* programming mode: drive the lines directly */
