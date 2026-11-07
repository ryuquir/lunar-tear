/* Helpers for mapper unit tests. Synthetic ROM: every byte of PRG 8K bank n is n (low 8 bits) and the byte at
 * offset 1 is n >> 8; every byte of CHR 1K bank n is n, offset 1 = n >> 8. So prg_bank(c, slot) / chr_bank(c, slot)
 * read back which bank is mapped. */
#pragma once
#include "cart.h"
#include "cartload.h"
#include "mapper.h"
#include "rom.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#define TM_CHECK(c, ...) do { (*checks)++; if (!(c)) { (*fails)++; printf("FAIL %s:%d: ", __FILE__, __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)
static uint8_t *tm_prg, *tm_chr;
/* mirroring: 0 H, 1 V, 2 four-screen. chr_kb 0 = CHR-RAM (chrram_kb). wram_kb includes battery RAM. */
static inline bool tm_load(cart_t *c, const mapper_desc_t *m, uint8_t sub, uint32_t prg_kb, uint32_t chr_kb, uint32_t chrram_kb, uint32_t wram_kb, uint8_t mirroring) {
    free(tm_prg); free(tm_chr);
    tm_prg = malloc(prg_kb * 1024 + 1); tm_chr = malloc(chr_kb * 1024 + 1024);
    for (uint32_t i = 0; i < prg_kb * 1024; i++) { uint32_t b = i >> 13; tm_prg[i] = (i & 0x1FFF) == 1 ? (uint8_t)(b >> 8) : (uint8_t)b; }
    for (uint32_t i = 0; i < chr_kb * 1024; i++) { uint32_t b = i >> 10; tm_chr[i] = (i & 0x3FF) == 1 ? (uint8_t)(b >> 8) : (uint8_t)b; }
    rom_info_t info; memset(&info, 0, sizeof info);
    info.source = ROM_SRC_DB; info.mapper = m->id; info.submapper = sub; info.mirroring = mirroring;
    info.prg_size = prg_kb * 1024; info.chr_size = chr_kb * 1024; info.chr_ram_size = chrram_kb * 1024; info.wram_size = wram_kb * 1024;
    /* load with a mapper the registry knows, then attach the descriptor under test */
    rom_info_t i0 = info; i0.mapper = 0;
    if (cart_load_ext(c, tm_prg, chr_kb ? tm_chr : NULL, &i0, NULL) != LOAD_OK) return false;
    c->mirroring = mirroring == 0 ? MIRROR_H : mirroring == 1 ? MIRROR_V : MIRROR_4;
    return mapper_attach_desc(c, m, sub);
}
static inline uint32_t tm_prg_bank(const cart_t *c, unsigned slot /* 0..7 = $0000..$E000 */) { const uint8_t *p = c->prg_map[slot]; return p ? (uint32_t)(p[0] | (p[1] << 8)) : 0xFFFFFFFFu; }
static inline uint32_t tm_chr_bank(const cart_t *c, unsigned slot /* 0..7 */) { const uint8_t *p = c->chr_map[slot]; return p ? (uint32_t)(p[0] | (p[1] << 8)) : 0xFFFFFFFFu; }
/* CIRAM page of nametable n, or -1 when a cartridge pointer is mapped */
static inline int tm_nt(const cart_t *c, unsigned n) { return c->nt_map[n] ? -1 : c->nt_ciram_a10[n]; }
