#pragma once
#include "../core/profile.h"
/* Flash ROM slot: [cart_profile_t, padded to 256 bytes][image]. A bare .nes image burned at the slot start also works. */
const uint8_t *romslot_image(uint32_t *len_out, const cart_profile_t **profile_out);
