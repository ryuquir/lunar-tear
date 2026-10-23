#include "cartload.h"
#include "mapper.h"
#include "audio/expaudio.h"
#include <string.h>

static uint8_t rom_pool[FC_ROM_POOL_SIZE] __attribute__((aligned(4)));
static uint8_t ram_pool[FC_RAM_POOL_SIZE] __attribute__((aligned(4)));

uint32_t cart_rom_pool_size(void) { return FC_ROM_POOL_SIZE; }
const char *cart_load_strerror(load_result_t r) {
    switch (r) { case LOAD_OK: return "ok"; case LOAD_ERR_INSPECT: return "unrecognised image"; case LOAD_ERR_TOO_BIG: return "ROM larger than SRAM pool";
                 case LOAD_ERR_MAPPER: return "unsupported mapper"; case LOAD_ERR_RAM: return "RAM pool exhausted"; }
    return "?";
}

static uint32_t mapper_exram_need(uint16_t mapper) {
    switch (mapper) { case 5: return 1024; case 19: return 128; case 119: return 8192; default: return 0; }
}

load_result_t cart_load(cart_t *c, const uint8_t *img, uint32_t len, const cart_profile_t *profile, rom_info_t *info_out) {
    rom_info_t info;
    if (!rom_inspect(img, len, &info)) { if (info_out) *info_out = info; return LOAD_ERR_INSPECT; }
    /* profile overrides */
    uint16_t mapper = info.mapper; uint8_t sub = info.submapper, mirror = info.mirroring;
    uint32_t wram = info.wram_size + info.sram_size, chrram = info.chr_ram_size;
    if (profile && profile_validate(profile)) {
        if (profile->mapper != 0xFFFF) mapper = profile->mapper;
        if (profile->submapper != 0xFF) sub = profile->submapper;
        if (profile->mirroring != 0xFF) mirror = profile->mirroring;
        if (profile->wram_kb != 0xFF) wram = (uint32_t)profile->wram_kb * 1024u;
        if (profile->chr_ram_kb != 0xFF) chrram = (uint32_t)profile->chr_ram_kb * 1024u;
    }
    if (info.prg_size + info.chr_size > FC_ROM_POOL_SIZE) { if (info_out) *info_out = info; return LOAD_ERR_TOO_BIG; }

    memset(c, 0, sizeof *c);
    memcpy(rom_pool, img + info.data_offset, info.prg_size);
    c->prg_rom = rom_pool; c->prg_size = info.prg_size; c->prg_pages = info.prg_size >> PRG_PAGE_SHIFT;
    if (info.chr_size) {
        memcpy(rom_pool + info.prg_size, img + info.data_offset + info.prg_size, info.chr_size);
        c->chr = rom_pool + info.prg_size; c->chr_size = info.chr_size; c->chr_is_ram = false;
    }
    /* RAM pool carve-up */
    uint32_t off = 0;
    if (wram == 0 && (mapper == 1 || mapper == 4 || mapper == 5 || mapper == 19 || mapper == 69 || mapper == 85 || mapper == 24 || mapper == 26 || mapper == 0 || mapper == 2 || mapper == 3)) wram = 8192; /* be generous: many iNES headers omit it */
    if (wram > 32768) wram = 32768;
    if (wram) { c->wram = ram_pool + off; c->wram_size = wram; off += wram; }
    if (!info.chr_size) {
        if (chrram == 0) chrram = 8192;
        if (chrram > 32768) chrram = 32768;
        if (off + chrram > FC_RAM_POOL_SIZE) return LOAD_ERR_RAM;
        c->chr = ram_pool + off; c->chr_size = chrram; c->chr_is_ram = true; off += chrram;
    }
    c->chr_pages = c->chr_size >> CHR_PAGE_SHIFT;
    uint32_t ex = mapper_exram_need(mapper);
    if (ex) { if (off + ex > FC_RAM_POOL_SIZE) return LOAD_ERR_RAM; c->exram = ram_pool + off; off += ex; }
    if (mirror == 2 || mapper == 19 || mapper == 68 || mapper == 5) { if (off + 2048 > FC_RAM_POOL_SIZE) return LOAD_ERR_RAM; c->extvram = ram_pool + off; off += 2048; }
    memset(ram_pool, 0, off);

    c->battery = info.battery; c->bus_conflicts = info.bus_conflicts; c->system = info.system;
    c->mirroring = (mirror == 0) ? MIRROR_H : (mirror == 1) ? MIRROR_V : (mirror == 2) ? MIRROR_4 : MIRROR_1A;
    if (!mapper_attach(c, mapper, sub)) { if (info_out) *info_out = info; return LOAD_ERR_MAPPER; }

    /* Expansion audio: mapper-native chips unless the profile says otherwise. */
    expaudio_slot_t slots[PROFILE_MAX_AUDIO]; unsigned n = 0;
    expaudio_reset(c);
    if (profile && profile_validate(profile) && !(profile->flags & PF_DISABLE_AUDIO)) {
        for (unsigned i = 0; i < PROFILE_MAX_AUDIO; i++) if (profile->audio[i].chip) {
            slots[n].chip = profile->audio[i].chip; slots[n].exclusive = profile->audio[i].exclusive; slots[n].base = profile->audio[i].base; slots[n].volume = profile->audio_volume[i]; n++;
        }
    }
    if (n == 0 && !(profile && profile_validate(profile) && (profile->flags & PF_DISABLE_AUDIO))) {
        uint8_t chip = 0;
        switch (mapper) { case 24: case 26: chip = AUDIO_VRC6; break; case 85: chip = AUDIO_VRC7; break; case 5: chip = AUDIO_MMC5; break;
                          case 19: chip = AUDIO_N163; break; case 69: chip = AUDIO_S5B; break; default: break; }
        if (chip) { slots[0].chip = chip; slots[0].exclusive = 0; slots[0].base = 0; slots[0].volume = 128; n = 1; }
    }
    expaudio_configure(c, slots, n);
    if (info_out) *info_out = info;
    return LOAD_OK;
}
