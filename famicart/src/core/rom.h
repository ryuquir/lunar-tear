/* ROM image inspection: iNES / NES 2.0 header parsing, CRC32 database lookup,
 * headerless heuristics. Produces a rom_info_t that cart_load() consumes. */
#pragma once
#include "fc_types.h"

typedef enum {
    ROM_SRC_NONE = 0,
    ROM_SRC_DB,          /* matched CRC32 in the built-in database (authoritative) */
    ROM_SRC_NES20,       /* NES 2.0 header */
    ROM_SRC_INES,        /* iNES 1.x header */
    ROM_SRC_HEURISTIC,   /* headerless image, guessed from size/content */
} rom_source_t;

typedef struct {
    rom_source_t source;
    bool     has_header;
    uint16_t mapper;
    uint8_t  submapper;
    uint8_t  mirroring;     /* 0 H, 1 V, 2 four-screen, 3 single */
    bool     battery;
    bool     bus_conflicts;
    uint8_t  system;        /* 0 NTSC, 1 PAL, 2 Famicom(=NTSC timing) */
    uint32_t prg_size;      /* bytes */
    uint32_t chr_size;      /* bytes (0 => CHR-RAM) */
    uint32_t chr_ram_size;  /* bytes */
    uint32_t wram_size;     /* bytes, volatile */
    uint32_t sram_size;     /* bytes, battery */
    uint32_t trainer_size;
    uint32_t data_offset;   /* offset of PRG data inside the image */
    uint32_t crc32;         /* over PRG+CHR */
    uint32_t file_crc32;    /* over the whole image incl. header */
    char     note[48];
} rom_info_t;

uint32_t fc_crc32(uint32_t crc, const uint8_t *p, size_t n);

/* Inspect an image in memory (flash or RAM). Returns false when nothing usable was found. */
bool rom_inspect_header(const uint8_t hdr[16], uint32_t data_len, uint32_t data_crc, rom_info_t *out);
bool rom_inspect(const uint8_t *img, uint32_t len, rom_info_t *out);

/* Database lookup by PRG+CHR CRC32. Returns NULL when unknown. */
struct romdb_entry; 
const void *romdb_lookup(uint32_t crc);
