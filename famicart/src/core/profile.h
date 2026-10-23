/* Cartridge profile: what the firmware should *behave as*, independent of what the
 * ROM header says. Lets the user combine e.g. mapper MMC5 with VRC7 audio.
 *
 * Stored (optionally) right after the ROM image in flash, see tools/rom2uf2.py.
 */
#pragma once
#include "fc_types.h"

#define PROFILE_MAGIC 0x50434346u  /* "FCCP" */
#define PROFILE_VERSION 1

typedef enum {
    AUDIO_NONE = 0,
    AUDIO_VRC6,
    AUDIO_VRC7,
    AUDIO_MMC5,
    AUDIO_N163,
    AUDIO_S5B,     /* Sunsoft 5B (YM2149 subset) */
    AUDIO_FDS,
    AUDIO_CHIP_COUNT
} audio_chip_t;

#define PROFILE_MAX_AUDIO 4

typedef struct {
    uint8_t  chip;        /* audio_chip_t */
    uint8_t  exclusive;   /* 1: writes to the chip's registers are NOT forwarded to the mapper */
    uint16_t base;        /* 0 = native register addresses; otherwise relocate the chip's register window here */
} profile_audio_t;

typedef struct {
    uint32_t magic;
    uint8_t  version;
    uint8_t  flags;              /* PF_* */
    uint16_t mapper;             /* 0xFFFF = keep auto-detected */
    uint8_t  submapper;          /* 0xFF  = keep auto-detected */
    uint8_t  mirroring;          /* 0xFF  = keep */
    uint8_t  wram_kb;            /* 0xFF  = keep */
    uint8_t  chr_ram_kb;         /* 0xFF  = keep */
    profile_audio_t audio[PROFILE_MAX_AUDIO];
    uint8_t  audio_volume[PROFILE_MAX_AUDIO]; /* 0..255, 128 = nominal */
    uint8_t  reserved[12];
    uint32_t crc;                /* CRC32 of everything above */
} cart_profile_t;

#define PF_FORCE_MAPPER   0x01
#define PF_DISABLE_AUDIO  0x02   /* ignore the mapper's own expansion audio */
#define PF_PAL            0x04

void profile_default(cart_profile_t *p);
bool profile_validate(const cart_profile_t *p);
