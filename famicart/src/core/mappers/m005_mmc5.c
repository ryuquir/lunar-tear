/* MMC5 (mapper 5). Scanline detection follows the real chip: three consecutive PPU
 * reads of the same nametable address mark the start of a scanline; in-frame status
 * drops after ~3 CPU cycles without PPU reads. Audio ($5000-$5015) is routed to the
 * expansion-audio layer. */
#include "../mapper.h"
#include "../audio/expaudio.h"
#include "mmc5.h"
#include <string.h>

static uint8_t fill_page[1024];

static void mmc5_sync_prg(cart_t *c) {
    mmc5_state_t *s = &c->s.mmc5;
    /* $6000 */
    cart_set_wram_6000(c, s->prg_bank[0] & 7, (s->prg_ram_protect1 == 2 && s->prg_ram_protect2 == 1));
    #define ROM(b) ((b) & 0x80)
    switch (s->prg_mode & 3) {
    case 0: cart_set_prg32k(c, (s->prg_bank[4] & 0x7F) >> 2); break;
    case 1:
        if (ROM(s->prg_bank[2])) cart_set_prg16k(c, 0, (s->prg_bank[2] & 0x7F) >> 1);
        else { uint8_t *w = c->wram + ((((uint32_t)s->prg_bank[2] & 6) << 13) % (c->wram_size ? c->wram_size : 1)); c->prg_map[4] = w; c->prg_wmap[4] = w; c->prg_map[5] = w + 8192; c->prg_wmap[5] = w + 8192; }
        cart_set_prg16k(c, 1, (s->prg_bank[4] & 0x7F) >> 1); break;
    case 2:
        if (ROM(s->prg_bank[2])) cart_set_prg16k(c, 0, (s->prg_bank[2] & 0x7F) >> 1);
        else { uint8_t *w = c->wram + ((((uint32_t)s->prg_bank[2] & 6) << 13) % (c->wram_size ? c->wram_size : 1)); c->prg_map[4] = w; c->prg_wmap[4] = w; c->prg_map[5] = w + 8192; c->prg_wmap[5] = w + 8192; }
        if (ROM(s->prg_bank[3])) cart_set_prg8k(c, 2, s->prg_bank[3] & 0x7F);
        else { uint8_t *w = c->wram + ((((uint32_t)s->prg_bank[3] & 7) << 13) % (c->wram_size ? c->wram_size : 1)); c->prg_map[6] = w; c->prg_wmap[6] = w; }
        cart_set_prg8k(c, 3, s->prg_bank[4] & 0x7F); break;
    default:
        for (unsigned i = 0; i < 3; i++) {
            uint8_t b = s->prg_bank[1 + i];
            if (ROM(b)) cart_set_prg8k(c, i, b & 0x7F);
            else { uint8_t *w = c->wram + ((((uint32_t)b & 7) << 13) % (c->wram_size ? c->wram_size : 1)); c->prg_map[4 + i] = w; c->prg_wmap[4 + i] = w; }
        }
        cart_set_prg8k(c, 3, s->prg_bank[4] & 0x7F); break;
    }
    #undef ROM
    if (!(s->prg_ram_protect1 == 2 && s->prg_ram_protect2 == 1)) for (unsigned i = 4; i < 8; i++) c->prg_wmap[i] = NULL;
}
/* CHR: both register sets are turned into page pointers when they are written, so the PPU-side hook only picks
 * one (it runs for every pattern fetch on rev E's PPU MCU). Set A feeds sprites and set B the background while
 * 8x16 sprites are on and the PPU is rendering; otherwise the last set written is used for every fetch. */
static void mmc5_calc_set(cart_t *c, unsigned set) {
    mmc5_state_t *s = &c->s.mmc5;
    uint8_t *save[8]; uint8_t wm = c->chr_wmask;
    for (unsigned i = 0; i < 8; i++) save[i] = c->chr_map[i];
    uint32_t up = (uint32_t)s->chr_upper << 8;
    if (set == 0) {
        switch (s->chr_mode & 3) {
        case 0: cart_set_chr8k(c, (int32_t)(up | s->chr_bank_a[7])); break;
        case 1: cart_set_chr4k(c, 0, (int32_t)(up | s->chr_bank_a[3])); cart_set_chr4k(c, 1, (int32_t)(up | s->chr_bank_a[7])); break;
        case 2: for (unsigned i = 0; i < 4; i++) cart_set_chr2k(c, i, (int32_t)(up | s->chr_bank_a[i * 2 + 1])); break;
        default: for (unsigned i = 0; i < 8; i++) cart_set_chr1k(c, i, (int32_t)(up | s->chr_bank_a[i])); break;
        }
    } else {
        switch (s->chr_mode & 3) {
        case 0: cart_set_chr8k(c, (int32_t)(up | s->chr_bank_b[3])); break;
        case 1: cart_set_chr4k(c, 0, (int32_t)(up | s->chr_bank_b[3])); cart_set_chr4k(c, 1, (int32_t)(up | s->chr_bank_b[3])); break;
        case 2: cart_set_chr2k(c, 0, (int32_t)(up | s->chr_bank_b[1])); cart_set_chr2k(c, 1, (int32_t)(up | s->chr_bank_b[3]));
                cart_set_chr2k(c, 2, (int32_t)(up | s->chr_bank_b[1])); cart_set_chr2k(c, 3, (int32_t)(up | s->chr_bank_b[3])); break;
        default: for (unsigned i = 0; i < 8; i++) cart_set_chr1k(c, i, (int32_t)(up | s->chr_bank_b[i & 3])); break;
        }
    }
    for (unsigned i = 0; i < 8; i++) { s->chr_set[set][i] = c->chr_map[i]; c->chr_map[i] = save[i]; }
    c->chr_wmask = wm;
}
static void mmc5_sync_chr(cart_t *c) {
    mmc5_state_t *s = &c->s.mmc5;
    mmc5_calc_set(c, 0); mmc5_calc_set(c, 1);
    unsigned use = s->last_chr_set ? 1 : 0;
    for (unsigned i = 0; i < 8; i++) cart_set_chr1k_ptr(c, i, s->chr_set[use][i], c->chr_is_ram);
}
static void mmc5_update_full(cart_t *c) {
    mmc5_state_t *s = &c->s.mmc5;
    s->split_on = (s->split_ctrl & 0x80) && c->exram && s->exram_mode < 2;
    uint8_t f = (s->exram_mode == 1 || s->split_on) ? 1 : 0;
    if (f != c->nt_full) { c->nt_full = f; c->tables_dirty = 1; }
}
static void mmc5_sync_nt(cart_t *c) {
    mmc5_state_t *s = &c->s.mmc5;
    for (unsigned i = 0; i < 4; i++) {
        switch ((s->nt_map >> (i * 2)) & 3) {
        case 0: cart_set_nt_ciram(c, i, 0); break;
        case 1: cart_set_nt_ciram(c, i, 1); break;
        case 2: c->nt_map[i] = (s->exram_mode < 2 && c->exram) ? c->exram : fill_page; if (s->exram_mode >= 2) c->nt_map[i] = fill_page; break; /* ExRAM as NT only in modes 0/1; modes 2/3 read as 0 (use fill page zeroed? real: $00) */
        default: c->nt_map[i] = fill_page; break;
        }
    }
}
static void mmc5_fill_update(cart_t *c) {
    mmc5_state_t *s = &c->s.mmc5;
    memset(fill_page, s->fill_tile, 960);
    uint8_t attr = (uint8_t)((s->fill_color & 3) * 0x55);
    memset(fill_page + 960, attr, 64);
}
static void mmc5_init(cart_t *c) {
    mmc5_state_t *s = &c->s.mmc5;
    memset(s, 0, sizeof *s);
    s->prg_mode = 3; s->chr_mode = 3; s->prg_bank[4] = 0xFF; s->prg_bank[3] = 0xFF; s->prg_bank[2] = 0xFF; s->prg_bank[1] = 0xFF;
    for (int i = 0; i < 8; i++) s->chr_bank_a[i] = (uint16_t)i;
    for (int i = 0; i < 4; i++) s->chr_bank_b[i] = (uint16_t)i;
    s->prg_ram_protect1 = 0; s->prg_ram_protect2 = 0; s->last_chr_set = 0;
    mmc5_fill_update(c); mmc5_sync_prg(c); mmc5_sync_chr(c); mmc5_sync_nt(c); mmc5_update_full(c);
}
static void mmc5_write(cart_t *c, uint16_t a, uint8_t v) {
    mmc5_state_t *s = &c->s.mmc5;
    if (a == 0x2000) { s->spr8x16 = (v >> 5) & 1; return; }
    if (a == 0x2001) { if (!(v & 0x18)) { s->in_frame = 0; } return; }
    if (a < 0x5000) return;
    if (a <= 0x5015) return; /* audio: consumed by router when enabled */
    if (a >= 0x5C00) { if (c->exram && s->exram_mode != 3) { if (s->exram_mode >= 2 || s->in_frame) c->exram[a & 0x3FF] = v; else c->exram[a & 0x3FF] = 0; } return; }
    switch (a) {
    case 0x5100: s->prg_mode = v & 3; mmc5_sync_prg(c); break;
    case 0x5101: s->chr_mode = v & 3; mmc5_sync_chr(c); break;
    case 0x5102: s->prg_ram_protect1 = v & 3; mmc5_sync_prg(c); break;
    case 0x5103: s->prg_ram_protect2 = v & 3; mmc5_sync_prg(c); break;
    case 0x5104: s->exram_mode = v & 3; mmc5_sync_nt(c); mmc5_update_full(c); break;
    case 0x5105: s->nt_map = v; mmc5_sync_nt(c); break;
    case 0x5106: s->fill_tile = v; mmc5_fill_update(c); break;
    case 0x5107: s->fill_color = v & 3; mmc5_fill_update(c); break;
    case 0x5113: case 0x5114: case 0x5115: case 0x5116: case 0x5117:
        s->prg_bank[a - 0x5113] = v; mmc5_sync_prg(c); break;
    case 0x5120: case 0x5121: case 0x5122: case 0x5123: case 0x5124: case 0x5125: case 0x5126: case 0x5127:
        s->chr_bank_a[a - 0x5120] = (uint16_t)v; s->last_chr_set = 0; mmc5_sync_chr(c); break;
    case 0x5128: case 0x5129: case 0x512A: case 0x512B:
        s->chr_bank_b[a - 0x5128] = (uint16_t)v; s->last_chr_set = 1; mmc5_sync_chr(c); break;
    case 0x5130: s->chr_upper = v & 3; break;   /* applies to the next bank write, as on the chip */
    case 0x5200: s->split_ctrl = v; mmc5_update_full(c); break;
    case 0x5201: s->split_scroll = v; break;
    case 0x5202: s->split_bank = v; break;
    case 0x5203: s->irq_scanline_cmp = v; break;
    case 0x5204: s->irq_enable = v >> 7; cart_irq(c, s->irq_enable && s->irq_pending); break;
    case 0x5205: s->mult_a = v; break;
    case 0x5206: s->mult_b = v; break;
    }
}
static uint8_t FC_FASTCODE(mmc5_peek)(cart_t *c, uint16_t a, uint8_t open) {
    mmc5_state_t *s = &c->s.mmc5;
    uint8_t v;
    if (a == 0x5204) return (uint8_t)((s->irq_pending << 7) | (s->in_frame << 6) | (open & 0x3F));
    if (a == 0x5205) return (uint8_t)((s->mult_a * s->mult_b) & 0xFF);
    if (a == 0x5206) return (uint8_t)((s->mult_a * s->mult_b) >> 8);
    if (a == 0x5015 && expaudio_cpu_read(c, a, &v)) return v;
    if (a >= 0x5C00 && c->exram) return (s->exram_mode >= 2) ? c->exram[a & 0x3FF] : open;
    return open;
}
static uint8_t FC_FASTCODE(mmc5_read)(cart_t *c, uint16_t a, uint8_t open) {
    mmc5_state_t *s = &c->s.mmc5;
    uint8_t v = mmc5_peek(c, a, open);
    if (a == 0x5204) { s->irq_pending = 0; cart_irq(c, false); }
    return v;
}
/* PPU side: scanline counter, 8x16 sprite CHR sets, ExRAM extended attributes, vertical split.
 * ppu_idle counts pattern-table fetches since the scanline was detected (at the dot-1 nametable fetch):
 *   0..63 background tiles 2..33, 64..79 sprites, 80..83 tiles 0..1 of the next line. */
void FC_FASTCODE(mmc5_scanline)(cart_t *c) {
    mmc5_state_t *s = &c->s.mmc5;
    if (!s->in_frame) { s->in_frame = 1; s->scanline = 0; }
    else {
        s->scanline++;
        if (s->scanline == s->irq_scanline_cmp && s->irq_scanline_cmp) { s->irq_pending = 1; if (s->irq_enable) cart_irq(c, true); }
        if (s->scanline >= 241) s->in_frame = 0;
    }
    s->ppu_idle = 0;
}
void mmc5_frame_end(cart_t *c) { c->s.mmc5.in_frame = 0; c->s.mmc5.match_count = 0; c->s.mmc5.a13_run = 0; }
/* rev E U3: only A13 and /RD are visible. Four nametable-area reads in a row happen once per line (dots 337, 339
 * and the dot-1/3 fetches of the next line); the third one is where the chip itself sees "three identical reads". */
bool FC_FASTCODE(mmc5_a13_read)(cart_t *c, bool a13) {
    mmc5_state_t *s = &c->s.mmc5;
    s->last_ppu_cycle = c->cpu_cycles;
    if (!a13) { s->a13_run = 0; return false; }
    if (++s->a13_run == 3) { mmc5_scanline(c); return true; }
    return false;
}
static inline int mmc5_tile(uint8_t pos) { return pos < 64 ? 2 + (pos >> 1) : pos >= 80 ? ((pos - 80) >> 1) : -1; }
static inline bool mmc5_in_split(const mmc5_state_t *s, int ti) {
    if (ti < 0) return false;
    unsigned th = s->split_ctrl & 0x1F, t = (unsigned)ti & 31;
    return (s->split_ctrl & 0x40) ? t >= th : t < th;
}
static inline unsigned mmc5_split_y(const mmc5_state_t *s, uint8_t pos) {
    unsigned line = s->scanline + (pos >= 80 ? 1u : 0u);
    return (s->split_scroll + line) % 240u;
}
static void FC_FASTCODE(mmc5_ppu_addr)(cart_t *c, uint16_t a) {
    mmc5_state_t *s = &c->s.mmc5;
    s->last_ppu_cycle = c->cpu_cycles;
    uint8_t pos = s->ppu_idle;
    if (a >= 0x2000 && a < 0x3F00) {
        if (a == s->last_ppu_addr) {
            if (++s->match_count == 2) { mmc5_scanline(c); s->match_count = 0; pos = 0; }
        } else { s->match_count = 0; s->last_ppu_addr = a; }
        if (!s->in_frame) return;
        bool attr = (a & 0x3FF) >= 0x3C0;
        int ti = mmc5_tile(pos);
        if (s->split_on && mmc5_in_split(s, ti)) {
            unsigned sy = mmc5_split_y(s, pos), t = (unsigned)ti & 31;
            if (!attr) { s->split_tile = c->exram[((sy >> 3) << 5) + t]; c->ppu_override = &s->split_tile; }
            else {
                uint8_t at = c->exram[0x3C0 + ((sy >> 5) << 3) + (t >> 2)];
                uint8_t pal = (uint8_t)((at >> ((((sy >> 4) & 1) << 2) | (((t >> 1) & 1) << 1))) & 3);
                s->split_attr = (uint8_t)(pal * 0x55); c->ppu_override = &s->split_attr;
            }
            return;
        }
        if (s->exram_mode == 1 && c->exram) {
            if (!attr) s->ex_byte = c->exram[a & 0x3FF];                          /* ex byte for this tile */
            else { s->attr_byte = (uint8_t)((s->ex_byte >> 6) * 0x55); c->ppu_override = &s->attr_byte; }
        }
    } else if (a < 0x2000) {
        if (s->in_frame) {
            bool spr = pos >= 64 && pos < 80;
            int ti = spr ? -1 : mmc5_tile(pos);
            uint32_t pages = c->chr_pages ? c->chr_pages : 1;
            if (!spr && s->split_on && mmc5_in_split(s, ti)) {
                unsigned off = (unsigned)s->split_tile * 16u + (a & 8u) + (mmc5_split_y(s, pos) & 7u);
                uint32_t page = ((uint32_t)s->split_bank * 4u + (off >> 10)) % pages;
                c->ppu_override = c->chr + (page << 10) + (off & 0x3FF);
            } else if (!spr && s->exram_mode == 1) {
                uint32_t bank4k = (uint32_t)(s->ex_byte & 0x3F) | ((uint32_t)s->chr_upper << 6);
                uint32_t page = (bank4k * 4u + ((a >> 10) & 3u)) % pages;
                c->ppu_override = c->chr + (page << 10) + (a & 0x3FF);
            } else if (s->spr8x16) {
                uint8_t *p = s->chr_set[spr ? 0 : 1][a >> 10];
                if (p) c->ppu_override = p + (a & 0x3FF);
            }
        }
        if (pos < 255) s->ppu_idle = (uint8_t)(pos + 1);
    }
}
static void FC_FASTCODE(mmc5_cpu_cycle)(cart_t *c) {
    mmc5_state_t *s = &c->s.mmc5;
    if (s->in_frame && (c->cpu_cycles - s->last_ppu_cycle) > 3) mmc5_frame_end(c);
}
const mapper_desc_t mapper_005 = { 5, "MMC5", MF_READ_LOW | MF_PPU_HOOK | MF_CPU_CYCLE | MF_SNOOP_PPU_REGS | MF_WRITE_6000, mmc5_init, mmc5_write, mmc5_read, mmc5_ppu_addr, mmc5_cpu_cycle, mmc5_peek };
