/* MMC1 core, shared by MMC1-based boards (NES-EVENT ...). */
#pragma once
#include "../cart.h"
void mmc1_init(cart_t *c);
void mmc1_write(cart_t *c, uint16_t a, uint8_t v);
void mmc1_sync(cart_t *c);
