#include "romcache.h"
#include <string.h>

uint32_t romcache_init(romcache_t *rc, const uint8_t *base, uint32_t size, uint8_t shift, uint8_t *pool, uint32_t pool_size, uint16_t *page_slot) {
    memset(rc, 0, sizeof *rc);
    rc->base = base; rc->size = size; rc->shift = shift; rc->pool = pool; rc->page_slot = page_slot;
    rc->pages = size >> shift;
    rc->nslots = pool_size >> shift; if (rc->nslots > RC_MAX_SLOTS) rc->nslots = RC_MAX_SLOTS;
    for (uint32_t i = 0; i < RC_MAX_SLOTS; i++) rc->slot_page[i] = 0xFFFF;
    for (uint32_t i = 0; i < rc->pages; i++) page_slot[i] = 0xFFFF;
    return rc->nslots;
}
bool romcache_fits(const romcache_t *rc) { return rc->pages <= rc->nslots; }

static void load_into(romcache_t *rc, uint32_t slot, uint32_t page) {
    if (rc->slot_page[slot] != 0xFFFF) rc->page_slot[rc->slot_page[slot]] = 0xFFFF;
    memcpy(rc->pool + (slot << rc->shift), rc->base + (page << rc->shift), 1u << rc->shift);
    rc->slot_page[slot] = (uint16_t)page; rc->page_slot[page] = (uint16_t)slot; rc->slot_use[slot] = ++rc->stamp; rc->loads++;
}
void romcache_preload(romcache_t *rc) {
    uint32_t n = rc->pages < rc->nslots ? rc->pages : rc->nslots;
    for (uint32_t p = 0; p < n; p++) load_into(rc, p, p);
}
static inline bool in_flash(const romcache_t *rc, const uint8_t *p) { return p >= rc->base && p < rc->base + rc->size; }
static inline bool in_pool(const romcache_t *rc, const uint8_t *p) { return p >= rc->pool && p < rc->pool + (rc->nslots << rc->shift); }

unsigned romcache_fix(romcache_t *rc, uint8_t **tbl, unsigned n) {
    unsigned miss = 0;
    for (unsigned i = 0; i < n; i++) {
        uint8_t *p = tbl[i];
        if (!p) continue;
        if (in_pool(rc, p)) { rc->slot_use[(uint32_t)(p - rc->pool) >> rc->shift] = ++rc->stamp; continue; }
        if (!in_flash(rc, p)) continue;
        uint32_t off = (uint32_t)(p - rc->base), page = off >> rc->shift;
        uint16_t s = rc->page_slot[page];
        if (s != 0xFFFF) { tbl[i] = rc->pool + ((uint32_t)s << rc->shift) + (off & ((1u << rc->shift) - 1)); rc->slot_use[s] = ++rc->stamp; rc->hits++; continue; }
        miss++; rc->misses++;
        bool queued = false; for (unsigned k = 0; k < rc->qn; k++) if (rc->q[k] == page) queued = true;
        if (!queued && rc->qn < RC_QUEUE) rc->q[rc->qn++] = (uint16_t)page;
    }
    return miss;
}
bool romcache_service(romcache_t *rc, uint8_t *const *live, unsigned nlive) {
    if (!rc->qn || !rc->nslots) return false;
    uint32_t page = rc->q[0]; memmove(rc->q, rc->q + 1, (size_t)(--rc->qn) * sizeof rc->q[0]);
    if (rc->page_slot[page] != 0xFFFF) return false;
    uint32_t best = 0xFFFFFFFFu, best_use = 0xFFFFFFFFu;
    for (uint32_t s = 0; s < rc->nslots; s++) {
        if (rc->slot_page[s] == 0xFFFF) { best = s; break; }
        bool pinned = false;
        for (unsigned i = 0; i < nlive && !pinned; i++) { const uint8_t *p = live[i]; if (p && in_pool(rc, p) && ((uint32_t)(p - rc->pool) >> rc->shift) == s) pinned = true; }
        if (!pinned && rc->slot_use[s] < best_use) { best_use = rc->slot_use[s]; best = s; }
    }
    if (best == 0xFFFFFFFFu) return false;
    load_into(rc, best, page);
    return true;
}
