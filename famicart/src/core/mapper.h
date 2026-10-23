/* Mapper interface + registry. */
#pragma once
#include "cart.h"

#define MF_WRITE_6000   0x01   /* route $6000-$7FFF writes to mapper->write even when WRAM is mapped */
#define MF_READ_LOW     0x02   /* mapper->read handles reads in $4020-$7FFF where prg_map[] is NULL */
#define MF_PPU_HOOK     0x04   /* needs ppu_addr() on every PPU access (A12 clocking, MMC2 latch, ...) */
#define MF_CPU_CYCLE    0x08   /* needs cpu_cycle() every M2 (cycle-based IRQ counters) */
#define MF_BUS_CONFLICT 0x10   /* discrete-logic board: written value ANDed with ROM byte */
#define MF_SNOOP_PPU_REGS 0x20 /* also receive CPU writes below $4020 (MMC5 watches $2000/$2001) */

typedef struct mapper_desc {
    uint16_t    id;
    const char *name;
    uint16_t    flags;
    void    (*init)     (cart_t *c);                                 /* power-on bank setup */
    void    (*write)    (cart_t *c, uint16_t addr, uint8_t v);        /* CPU write $4020-$FFFF */
    uint8_t (*read)     (cart_t *c, uint16_t addr, uint8_t open_bus); /* CPU read  $4020-$7FFF (slow path) */
    void    (*ppu_addr) (cart_t *c, uint16_t addr);                   /* PPU address observed */
    void    (*cpu_cycle)(cart_t *c);                                  /* one M2 cycle elapsed */
} mapper_desc_t;

const mapper_desc_t *mapper_find(uint16_t id);
unsigned             mapper_count(void);
const mapper_desc_t *mapper_at(unsigned i);

/* Attach + initialise a mapper on a loaded cartridge. Returns false when unsupported. */
bool mapper_attach(cart_t *c, uint16_t id, uint8_t submapper);

/* MMC3-style A12 rising-edge filter shared by several mappers. Returns true on a
 * qualified rising edge (A12 was low for >= min_low PPU-address observations). */
FC_INLINE bool mapper_a12_edge(uint8_t *state, uint16_t addr) {
    uint8_t now = (addr >> 12) & 1;
    bool rise = false;
    if (now) {
        if (*state >= 3) rise = true;   /* low for >= 3 fetches (~ 2 dots*3) */
        *state = 0x80;                  /* high */
    } else {
        if (*state & 0x80) *state = 1; else if (*state < 0x7F) (*state)++;
    }
    return rise;
}
