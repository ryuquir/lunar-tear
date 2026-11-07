/* rev E: SRAM page cache in front of ROM data that lives in the MCU's own QSPI flash (XIP).
 * Games whose PRG (U1) or CHR (U2) fit the pool are preloaded completely and never miss. Bigger games keep the
 * flash pointers in the mapper tables; romcache_fix() swaps every table entry whose page is cached for its SRAM copy
 * and queues the others, romcache_service() copies one queued page (called from the idle loop) -- so right after a
 * bank switch the bus is served straight from flash, and from SRAM a few hundred microseconds later.
 * Pages referenced by the live tables are never evicted. Portable: the host tests use a RAM array as "flash". */
#pragma once
#include <stdint.h>
#include <stdbool.h>

#define RC_MAX_SLOTS 512
#define RC_QUEUE     16

typedef struct {
    const uint8_t *base; uint32_t size;         /* flash image (PRG or CHR) */
    uint8_t  shift;                              /* page size = 1 << shift (13 for PRG, 10 for CHR) */
    uint8_t *pool; uint32_t nslots;
    uint16_t slot_page[RC_MAX_SLOTS];            /* page held by each slot, 0xFFFF = empty */
    uint32_t slot_use[RC_MAX_SLOTS];             /* LRU stamp */
    uint16_t *page_slot;                         /* page -> slot (0xFFFF = not cached), caller-provided, pages entries */
    uint32_t pages, stamp;
    uint16_t q[RC_QUEUE]; uint8_t qn;
    uint32_t hits, misses, loads;
} romcache_t;

/* page_slot must hold size >> shift entries. Returns the number of slots. */
uint32_t romcache_init(romcache_t *rc, const uint8_t *base, uint32_t size, uint8_t shift, uint8_t *pool, uint32_t pool_size, uint16_t *page_slot);
/* Copy pages 0..n-1 into the cache up front (all of them when the image fits). */
void romcache_preload(romcache_t *rc);
bool romcache_fits(const romcache_t *rc);
/* Replace flash pointers in tbl[0..n-1] by cached SRAM pointers; queue misses. Returns the number of misses. */
unsigned romcache_fix(romcache_t *rc, uint8_t **tbl, unsigned n);
/* Load one queued page. `live`/`nlive` = tables currently in use (pinned). Returns true when a page was loaded. */
bool romcache_service(romcache_t *rc, uint8_t *const *live, unsigned nlive);
