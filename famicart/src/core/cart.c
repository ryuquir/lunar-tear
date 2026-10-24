#include "cart.h"
#include "mapper.h"
#include "audio/expaudio.h"
#include <string.h>

/* ---------------- PRG ---------------- */
static inline uint32_t wrap_prg(const cart_t *c, int32_t bank, uint32_t pages) {
    if (pages == 0) return 0;
    int32_t b = bank % (int32_t)pages;
    if (b < 0) b += (int32_t)pages;
    return (uint32_t)b;
}

void cart_set_prg8k(cart_t *c, unsigned slot, int32_t bank) {
    uint32_t b = wrap_prg(c, bank, c->prg_pages);
    c->prg_map[4 + (slot & 3)]  = c->prg_rom + (b << PRG_PAGE_SHIFT);
    c->prg_wmap[4 + (slot & 3)] = NULL; c->tables_dirty = 1;
}
void cart_set_prg16k(cart_t *c, unsigned slot, int32_t bank) {
    uint32_t pages16 = c->prg_pages >> 1;
    uint32_t b = wrap_prg(c, bank, pages16 ? pages16 : 1);
    cart_set_prg8k(c, (slot & 1) * 2,     (int32_t)(b * 2));
    cart_set_prg8k(c, (slot & 1) * 2 + 1, (int32_t)(b * 2 + 1));
}
void cart_set_prg32k(cart_t *c, int32_t bank) {
    uint32_t pages32 = c->prg_pages >> 2;
    uint32_t b = wrap_prg(c, bank, pages32 ? pages32 : 1);
    for (unsigned i = 0; i < 4; i++) cart_set_prg8k(c, i, (int32_t)(b * 4 + i));
}
void cart_set_prg8k_6000(cart_t *c, int32_t bank) {
    uint32_t b = wrap_prg(c, bank, c->prg_pages);
    c->prg_map[3]  = c->prg_rom + (b << PRG_PAGE_SHIFT);
    c->prg_wmap[3] = NULL; c->tables_dirty = 1;
}
void cart_set_wram_6000(cart_t *c, uint32_t bank8k, bool writable) {
    if (!c->wram || c->wram_size == 0) { cart_unmap_6000(c); return; }
    uint32_t pages = c->wram_size >> PRG_PAGE_SHIFT; if (!pages) pages = 1;
    uint8_t *p = c->wram + ((bank8k % pages) << PRG_PAGE_SHIFT);
    c->prg_map[3]  = p;
    c->prg_wmap[3] = writable ? p : NULL; c->tables_dirty = 1;
}
void cart_unmap_6000(cart_t *c) { c->prg_map[3] = NULL; c->prg_wmap[3] = NULL; c->tables_dirty = 1; }

/* ---------------- CHR ---------------- */
void cart_set_chr1k(cart_t *c, unsigned slot, int32_t bank) {
    uint32_t b = wrap_prg(c, bank, c->chr_pages);
    slot &= 7;
    c->chr_map[slot] = c->chr + (b << CHR_PAGE_SHIFT);
    if (c->chr_is_ram) c->chr_wmask |= (uint8_t)(1u << slot); else c->chr_wmask &= (uint8_t)~(1u << slot);
    c->tables_dirty = 1;
}
void cart_set_chr2k(cart_t *c, unsigned slot, int32_t bank) {
    slot &= 3; cart_set_chr1k(c, slot * 2, bank * 2); cart_set_chr1k(c, slot * 2 + 1, bank * 2 + 1);
}
void cart_set_chr4k(cart_t *c, unsigned slot, int32_t bank) {
    slot &= 1; for (unsigned i = 0; i < 4; i++) cart_set_chr1k(c, slot * 4 + i, bank * 4 + (int32_t)i);
}
void cart_set_chr8k(cart_t *c, int32_t bank) { for (unsigned i = 0; i < 8; i++) cart_set_chr1k(c, i, bank * 8 + (int32_t)i); }
void cart_set_chr1k_ptr(cart_t *c, unsigned slot, uint8_t *p, bool writable) {
    slot &= 7; c->chr_map[slot] = p; c->tables_dirty = 1;
    if (writable) c->chr_wmask |= (uint8_t)(1u << slot); else c->chr_wmask &= (uint8_t)~(1u << slot);
}

/* ---------------- nametables ---------------- */
void cart_set_nt_ciram(cart_t *c, unsigned nt, unsigned page) { c->tables_dirty = 1; nt &= 3; c->nt_map[nt] = NULL; c->nt_ciram_a10[nt] = page & 1; }
void cart_set_nt_ptr(cart_t *c, unsigned nt, uint8_t *p) { c->tables_dirty = 1;
    nt &= 3;
    if (p) c->nt_map[nt] = p; else cart_set_mirroring(c, c->mirroring);
}
void cart_set_nt_chr1k(cart_t *c, unsigned nt, int32_t bank) { c->tables_dirty = 1;
    uint32_t b = wrap_prg(c, bank, c->chr_pages);
    c->nt_map[nt & 3] = c->chr + (b << CHR_PAGE_SHIFT);
}
void cart_set_mirroring(cart_t *c, mirroring_t m) { c->tables_dirty = 1;
    c->mirroring = m;
    switch (m) {
    case MIRROR_H:  cart_set_nt_ciram(c,0,0); cart_set_nt_ciram(c,1,0); cart_set_nt_ciram(c,2,1); cart_set_nt_ciram(c,3,1); break;
    case MIRROR_V:  cart_set_nt_ciram(c,0,0); cart_set_nt_ciram(c,1,1); cart_set_nt_ciram(c,2,0); cart_set_nt_ciram(c,3,1); break;
    case MIRROR_1A: for (unsigned i = 0; i < 4; i++) cart_set_nt_ciram(c,i,0); break;
    case MIRROR_1B: for (unsigned i = 0; i < 4; i++) cart_set_nt_ciram(c,i,1); break;
    case MIRROR_4:
        cart_set_nt_ciram(c,0,0); cart_set_nt_ciram(c,1,1);
        if (c->extvram) { c->nt_map[2] = c->extvram; c->nt_map[3] = c->extvram + 1024; }
        else { cart_set_nt_ciram(c,2,0); cart_set_nt_ciram(c,3,1); }
        break;
    }
}

/* ---------------- slow-path accessors (reference semantics) ---------------- */
uint8_t FC_FASTCODE(cart_cpu_read)(cart_t *c, uint16_t addr) {
    const uint8_t *p = c->prg_map[addr >> 13];
    uint8_t v;
    if (p) v = p[addr & 0x1FFF];
    else if (c->has_read_hook && addr >= 0x4020) v = c->mapper->read(c, addr, c->open_bus);
    else v = c->open_bus;
    c->open_bus = v;
    return v;
}
void FC_FASTCODE(cart_cpu_write)(cart_t *c, uint16_t addr, uint8_t v) {
    c->open_bus = v;
    if (c->audio_mask && expaudio_cpu_write(c, addr, v)) return;   /* exclusive audio register hit */
    if (addr < 0x4020) { if (c->mapper->flags & MF_SNOOP_PPU_REGS) c->mapper->write(c, addr, v); return; }
    uint8_t *w = c->prg_wmap[addr >> 13];
#if FC_VIRTUAL_ROM
    if (w && !((c->mapper->flags & MF_WRITE_6000) && addr < 0x8000)) return;   /* the external RAM chip took the write */
    if (c->mapper->write) c->mapper->write(c, addr, v);                        /* no bus-conflict AND: ROM is not readable here */
#else
    if (w && !((c->mapper->flags & MF_WRITE_6000) && addr < 0x8000)) { w[addr & 0x1FFF] = v; return; }
    if (c->mapper->write) {
        if ((c->mapper->flags & MF_BUS_CONFLICT) && c->bus_conflicts && addr >= 0x8000) {
            const uint8_t *p = c->prg_map[addr >> 13];
            if (p) v &= p[addr & 0x1FFF];
        }
        c->mapper->write(c, addr, v);
    }
#endif
}
uint8_t FC_FASTCODE(cart_ppu_read)(cart_t *c, uint16_t addr) {
    addr &= 0x3FFF;
    if (c->has_ppu_hook) { c->ppu_override = NULL; c->mapper->ppu_addr(c, addr); if (c->ppu_override) return *c->ppu_override; }
    if (addr < 0x2000) return c->chr_map[addr >> 10][addr & 0x3FF];
    if (addr < 0x3F00) {
        uint8_t *nt = c->nt_map[(addr >> 10) & 3];
        if (nt) return nt[addr & 0x3FF];
        return 0; /* console CIRAM: not visible to the cartridge */
    }
    return 0;
}
void FC_FASTCODE(cart_ppu_write)(cart_t *c, uint16_t addr, uint8_t v) {
    addr &= 0x3FFF;
    if (c->has_ppu_hook) c->mapper->ppu_addr(c, addr);
    if (addr < 0x2000) { if (c->chr_wmask & (1u << (addr >> 10))) c->chr_map[addr >> 10][addr & 0x3FF] = v; return; }
    if (addr < 0x3F00) { uint8_t *nt = c->nt_map[(addr >> 10) & 3]; if (nt) nt[addr & 0x3FF] = v; }
}
void FC_FASTCODE(cart_cpu_cycle)(cart_t *c) {
    c->cpu_cycles++;
    if (c->has_cpu_cycle_hook) c->mapper->cpu_cycle(c);
}
