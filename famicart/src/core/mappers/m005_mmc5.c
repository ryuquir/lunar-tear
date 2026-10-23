/* MMC5 (mapper 5). Scanline detection follows the real chip: three consecutive PPU
 * reads of the same nametable address mark the start of a scanline; in-frame status
 * drops after ~3 CPU cycles without PPU reads. Audio ($5000-$5015) is routed to the
 * expansion-audio layer. */
#include "../mapper.h"
#include "../audio/expaudio.h"
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
static void mmc5_sync_chr(cart_t *c, bool sprites /* use set A */) {
    mmc5_state_t *s = &c->s.mmc5;
    uint32_t up = (uint32_t)s->chr_upper << 8;
    if (sprites || !s->spr8x16) {
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
    mmc5_fill_update(c); mmc5_sync_prg(c); mmc5_sync_chr(c, true); mmc5_sync_nt(c);
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
    case 0x5101: s->chr_mode = v & 3; mmc5_sync_chr(c, s->last_chr_set == 0); break;
    case 0x5102: s->prg_ram_protect1 = v & 3; mmc5_sync_prg(c); break;
    case 0x5103: s->prg_ram_protect2 = v & 3; mmc5_sync_prg(c); break;
    case 0x5104: s->exram_mode = v & 3; mmc5_sync_nt(c); break;
    case 0x5105: s->nt_map = v; mmc5_sync_nt(c); break;
    case 0x5106: s->fill_tile = v; mmc5_fill_update(c); break;
    case 0x5107: s->fill_color = v & 3; mmc5_fill_update(c); break;
    case 0x5113: case 0x5114: case 0x5115: case 0x5116: case 0x5117:
        s->prg_bank[a - 0x5113] = v; mmc5_sync_prg(c); break;
    case 0x5120: case 0x5121: case 0x5122: case 0x5123: case 0x5124: case 0x5125: case 0x5126: case 0x5127:
        s->chr_bank_a[a - 0x5120] = (uint16_t)v; s->last_chr_set = 0; mmc5_sync_chr(c, true); break;
    case 0x5128: case 0x5129: case 0x512A: case 0x512B:
        s->chr_bank_b[a - 0x5128] = (uint16_t)v; s->last_chr_set = 1; mmc5_sync_chr(c, false); break;
    case 0x5130: s->chr_upper = v & 3; break;
    case 0x5200: s->split_ctrl = v; break;
    case 0x5201: s->split_scroll = v; break;
    case 0x5202: s->split_bank = v; break;
    case 0x5203: s->irq_scanline_cmp = v; break;
    case 0x5204: s->irq_enable = v >> 7; cart_irq(c, s->irq_enable && s->irq_pending); break;
    case 0x5205: s->mult_a = v; break;
    case 0x5206: s->mult_b = v; break;
    }
}
static uint8_t mmc5_read(cart_t *c, uint16_t a, uint8_t open) {
    mmc5_state_t *s = &c->s.mmc5;
    uint8_t v;
    if (a == 0x5204) { v = (uint8_t)((s->irq_pending << 7) | (s->in_frame << 6) | (open & 0x3F)); s->irq_pending = 0; cart_irq(c, false); return v; }
    if (a == 0x5205) return (uint8_t)((s->mult_a * s->mult_b) & 0xFF);
    if (a == 0x5206) return (uint8_t)((s->mult_a * s->mult_b) >> 8);
    if (a == 0x5015 && expaudio_cpu_read(c, a, &v)) return v;
    if (a >= 0x5C00 && c->exram) return (s->exram_mode >= 2) ? c->exram[a & 0x3FF] : open;
    return open;
}
/* PPU side: scanline counter, 8x16 sprite CHR set switching, ExRAM extended attributes.
 * fetch_pos counts pattern-table fetches since the start of the scanline:
 *   0..63  background (32 tiles x 2 planes)   64..79 sprites (8 x 2)   80..83 next-line prefetch. */
static void mmc5_ppu_addr(cart_t *c, uint16_t a) {
    mmc5_state_t *s = &c->s.mmc5;
    s->last_ppu_cycle = c->cpu_cycles;
    if (a >= 0x2000 && a < 0x3F00) {
        if (a == s->last_ppu_addr) {
            if (++s->match_count == 2) {   /* third consecutive identical NT read => new scanline */
                if (!s->in_frame) { s->in_frame = 1; s->scanline = 0; }
                else {
                    s->scanline++;
                    if (s->scanline == s->irq_scanline_cmp && s->irq_scanline_cmp) { s->irq_pending = 1; if (s->irq_enable) cart_irq(c, true); }
                    if (s->scanline >= 241) s->in_frame = 0;
                }
                s->ppu_idle = 0;             /* fetch_pos := 0 */
                s->match_count = 0;
            }
        } else { s->match_count = 0; s->last_ppu_addr = a; }
        if (s->exram_mode == 1 && c->exram && c->nt_map[(a >> 10) & 3] == c->exram) {
            if ((a & 0x3FF) < 0x3C0) s->split_bank = c->exram[a & 0x3FF];          /* ex byte for the next pattern fetch */
            else { static uint8_t attr_byte; attr_byte = (uint8_t)((s->split_bank >> 6) * 0x55); c->ppu_override = &attr_byte; }
        }
    } else if (a < 0x2000) {
        uint8_t pos = s->ppu_idle;
        bool spr = (s->spr8x16 && s->in_frame && pos >= 64 && pos < 80);
        if (s->spr8x16 && s->in_frame) mmc5_sync_chr(c, spr);
        if (s->exram_mode == 1 && s->in_frame && !spr) {
            uint32_t bank4k = (uint32_t)(s->split_bank & 0x3F) | ((uint32_t)s->chr_upper << 6);
            uint32_t pages = c->chr_pages ? c->chr_pages : 1;
            const uint8_t *p = c->chr + (((bank4k * 4 + ((a >> 10) & 3)) % pages) << 10);
            static uint8_t ex_byte; ex_byte = p[a & 0x3FF]; c->ppu_override = &ex_byte;
        }
        if (pos < 255) s->ppu_idle = (uint8_t)(pos + 1);
    }
}
static void mmc5_cpu_cycle(cart_t *c) {
    mmc5_state_t *s = &c->s.mmc5;
    if (s->in_frame && (c->cpu_cycles - s->last_ppu_cycle) > 3) { s->in_frame = 0; s->match_count = 0; }
}
const mapper_desc_t mapper_005 = { 5, "MMC5", MF_READ_LOW | MF_PPU_HOOK | MF_CPU_CYCLE | MF_SNOOP_PPU_REGS | MF_WRITE_6000, mmc5_init, mmc5_write, mmc5_read, mmc5_ppu_addr, mmc5_cpu_cycle };
