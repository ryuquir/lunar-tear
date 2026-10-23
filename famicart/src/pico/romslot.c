#include "romslot.h"
#include "board.h"
#include "../core/rom.h"
#include "hardware/flash.h"
#include <string.h>

#define ROMSLOT_HDR 256u

const uint8_t *romslot_image(uint32_t *len_out, const cart_profile_t **profile_out) {
    const uint8_t *slot = (const uint8_t *)(XIP_BASE + FC_FLASH_ROM_SLOT);
    const cart_profile_t *p = (const cart_profile_t *)slot;
    const uint8_t *img;
    if (profile_validate(p)) { img = slot + ROMSLOT_HDR; *profile_out = p; }
    else { img = slot; *profile_out = NULL; }
    /* Length: from the header when present, else scan for the end of programmed flash (0xFF fill). */
    uint32_t max = FC_FLASH_ROM_SLOT_MAX - (uint32_t)(img - slot);
    rom_info_t info;
    uint32_t len = 0;
    if (memcmp(img, "NES\x1a", 4) == 0) {
        uint8_t prg = img[4], chr = img[5];
        bool nes2 = (img[7] & 0x0C) == 0x08;
        uint32_t ps = nes2 ? (((uint32_t)(img[9] & 0x0F) << 8 | prg) * 16384u) : (uint32_t)prg * 16384u;
        uint32_t cs = nes2 ? (((uint32_t)(img[9] >> 4) << 8 | chr) * 8192u) : (uint32_t)chr * 8192u;
        len = 16 + ((img[6] & 4) ? 512u : 0u) + ps + cs;
    } else {
        /* headerless: find last non-0xFF 4K page */
        uint32_t end = max;
        while (end > 0) { bool blank = true; for (uint32_t i = 0; i < 4096 && blank; i += 64) if (img[end - 4096 + i] != 0xFF) blank = false; if (!blank) break; end -= 4096; }
        /* round down to a size the inspector understands */
        len = end & ~0x3FFFu;
    }
    if (len > max) len = max;
    (void)info;
    *len_out = len;
    return img;
}
