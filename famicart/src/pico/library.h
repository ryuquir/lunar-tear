/* rev D ROM library: index of the images stored in the external PRG/CHR flashes, kept in U1's QSPI flash. */
#pragma once
#include <stdint.h>
#include "../core/profile.h"

#define LIB_MAGIC      0x42494C46u   /* "FLIB" */
#define LIB_MAX        64
#define LIB_ENTRY_SIZE 256

typedef struct {
    uint32_t magic;             /* LIB_MAGIC when the slot is used */
    uint32_t prg_off, prg_size; /* byte offsets/lengths in the PRG flash (64 MB, byte addressed) */
    uint32_t chr_off, chr_size; /* in the CHR flash; chr_size 0 = CHR-RAM game */
    uint32_t data_crc;          /* CRC32 of PRG+CHR data (database key) */
    uint8_t  header[16];        /* iNES / NES 2.0 header as received */
    uint8_t  flags;             /* bit0: valid profile */
    uint8_t  reserved[3];
    char     name[48];
    cart_profile_t profile;
} lib_entry_t;                  /* 48 + 16 + ... < 256 */

typedef struct {
    uint32_t magic;             /* LIB_MAGIC */
    uint32_t current;           /* slot booted at power-up */
    uint32_t prg_used, chr_used;/* allocation high-water marks (bytes) */
    uint8_t  reserved[240];
} lib_header_t;                 /* 256 bytes */

_Static_assert(sizeof(lib_entry_t) <= LIB_ENTRY_SIZE, "lib_entry_t too big");
_Static_assert(sizeof(lib_header_t) == 256, "lib_header_t size");
