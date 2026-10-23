/* Cartridge state shared between the bus front-end (PIO/ISR) and the mapper logic.
 *
 * Fast-path contract (used by the bus service loops, must stay O(1)):
 *   CPU read  A ($4020-$FFFF):  p = prg_map[A>>13]; p ? p[A&0x1FFF] : mapper->read()
 *   CPU write A:                w = prg_wmap[A>>13]; w ? w[A&0x1FFF]=v : mapper->write()
 *   PPU read  A ($0000-$1FFF):  chr_map[A>>10][A&0x3FF]
 *   PPU read  A ($2000-$2FFF):  nt_map[(A>>10)&3] ? that : console CIRAM (bank = nt_ciram_a10[])
 */
#pragma once
#include "fc_types.h"

#define PRG_PAGE_SHIFT 13          /* 8 KiB PRG granularity */
#define PRG_PAGE_SIZE  (1u << PRG_PAGE_SHIFT)
#define CHR_PAGE_SHIFT 10          /* 1 KiB CHR granularity */
#define CHR_PAGE_SIZE  (1u << CHR_PAGE_SHIFT)

typedef enum {
    MIRROR_H = 0,   /* horizontal arrangement: CIRAM A10 = PPU A11 */
    MIRROR_V,       /* vertical arrangement:   CIRAM A10 = PPU A10 */
    MIRROR_1A,      /* single screen, CIRAM page 0 */
    MIRROR_1B,      /* single screen, CIRAM page 1 */
    MIRROR_4,       /* four screen: $2800-$2FFF from cartridge VRAM */
} mirroring_t;

struct cart;
struct mapper_desc;

/* Per-mapper state. Each mapper owns one member; keep every struct <= 512 bytes. */
#include "mapper_state.h"

typedef struct cart {
    /* ---- fast path tables (hot, keep at top of struct) ---- */
    const uint8_t *prg_map[8];
    uint8_t       *prg_wmap[8];
    uint8_t       *chr_map[8];
    uint8_t       *nt_map[4];
    uint8_t        nt_ciram_a10[4];
    uint8_t        chr_wmask;          /* bit i set -> chr_map[i] is writable (CHR-RAM) */
    volatile uint8_t irq_line;         /* 1 = assert /IRQ */
    uint8_t        has_ppu_hook;       /* mapper->ppu_addr must be called on every PPU address */
    uint8_t        has_cpu_cycle_hook; /* mapper->cpu_cycle must be called every M2 */
    uint8_t        has_read_hook;      /* mapper->read must be consulted when prg_map[] is NULL */
    const uint8_t *ppu_override;       /* set by ppu_addr hook: serve this byte instead of the table lookup */
    uint8_t        audio_mask;         /* bitmask of enabled expansion audio chips (see profile.h) */

    /* ---- ROM / RAM backing storage ---- */
    const uint8_t *prg_rom;  uint32_t prg_size;   uint32_t prg_pages;  /* 8K pages */
    uint8_t       *chr;      uint32_t chr_size;   uint32_t chr_pages;  /* 1K pages */
    bool           chr_is_ram;
    uint8_t       *wram;     uint32_t wram_size;  bool battery;
    uint8_t       *extvram;  /* 2 KiB for four-screen / mapper nametables, may be NULL */
    uint8_t       *exram;    /* up to 1 KiB mapper RAM (MMC5 ExRAM, N163 RAM, ...), may be NULL */

    /* ---- identity ---- */
    const struct mapper_desc *mapper;
    uint16_t  mapper_id;
    uint8_t   submapper;
    mirroring_t mirroring;
    bool      bus_conflicts;
    uint8_t   system;        /* 0 NTSC 1 PAL 2 Famicom */

    /* ---- misc ---- */
    uint32_t  cpu_cycles;    /* free running M2 counter (wraps) */
    uint8_t   open_bus;      /* last value seen on the CPU data bus */

    mapper_state_t s;
} cart_t;

/* ---- helpers for mappers (bank numbers wrap modulo ROM size) ---- */
void cart_set_prg8k (cart_t *c, unsigned slot /*0..3 => $8000,$A000,$C000,$E000*/, int32_t bank);
void cart_set_prg16k(cart_t *c, unsigned slot /*0..1 => $8000,$C000*/, int32_t bank);
void cart_set_prg32k(cart_t *c, int32_t bank);
void cart_set_prg8k_6000(cart_t *c, int32_t bank);            /* map PRG-ROM at $6000-$7FFF (read only) */
void cart_set_wram_6000(cart_t *c, uint32_t bank8k, bool writable);
void cart_unmap_6000(cart_t *c);

void cart_set_chr1k(cart_t *c, unsigned slot /*0..7*/, int32_t bank);
void cart_set_chr2k(cart_t *c, unsigned slot /*0..3*/, int32_t bank);
void cart_set_chr4k(cart_t *c, unsigned slot /*0..1*/, int32_t bank);
void cart_set_chr8k(cart_t *c, int32_t bank);
void cart_set_chr1k_ptr(cart_t *c, unsigned slot, uint8_t *p, bool writable);

void cart_set_mirroring(cart_t *c, mirroring_t m);
void cart_set_nt_ptr(cart_t *c, unsigned nt /*0..3*/, uint8_t *p);  /* NULL => back to CIRAM per mirroring */
void cart_set_nt_ciram(cart_t *c, unsigned nt, unsigned page /*0/1*/);
void cart_set_nt_chr1k(cart_t *c, unsigned nt, int32_t bank);        /* nametable from CHR (N163, MMC5-like) */

FC_INLINE void cart_irq(cart_t *c, bool on) { c->irq_line = on ? 1 : 0; }

/* Open-bus-safe read of a mapped CPU address (slow path, used by tests and the ISR fallback). */
uint8_t cart_cpu_read (cart_t *c, uint16_t addr);
void    cart_cpu_write(cart_t *c, uint16_t addr, uint8_t v);
uint8_t cart_ppu_read (cart_t *c, uint16_t addr);
void    cart_ppu_write(cart_t *c, uint16_t addr, uint8_t v);
void    cart_cpu_cycle(cart_t *c);
