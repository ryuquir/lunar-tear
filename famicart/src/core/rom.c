#include "rom.h"
#include "romdb_gen.h"
#include <string.h>
#include <stdio.h>

/* CRC32 (IEEE 802.3), table-less bitwise variant with a small 16-entry nibble table. */
static const uint32_t crc_nib[16] = {
    0x00000000,0x1DB71064,0x3B6E20C8,0x26D930AC,0x76DC4190,0x6B6B51F4,0x4DB26158,0x5005713C,
    0xEDB88320,0xF00F9344,0xD6D6A3E8,0xCB61B38C,0x9B64C2B0,0x86D3D2D4,0xA00AE278,0xBDBDF21C };
uint32_t fc_crc32(uint32_t crc, const uint8_t *p, size_t n) {
    crc = ~crc;
    while (n--) {
        crc ^= *p++;
        crc = crc_nib[crc & 15] ^ (crc >> 4);
        crc = crc_nib[crc & 15] ^ (crc >> 4);
    }
    return ~crc;
}

const void *romdb_lookup(uint32_t crc) {
    int lo = 0, hi = ROMDB_COUNT - 1;
    while (lo <= hi) {
        int mid = (lo + hi) >> 1;
        uint32_t k = romdb_table[mid].crc;
        if (k == crc) return &romdb_table[mid];
        if (k < crc) lo = mid + 1; else hi = mid - 1;
    }
    return NULL;
}

static uint32_t nes2_size(uint8_t lsb, uint8_t msb_nibble, uint32_t unit) {
    if (msb_nibble == 0xF) { /* exponent-multiplier notation */
        uint32_t e = lsb >> 2, m = (lsb & 3) * 2 + 1;
        return (1u << e) * m;
    }
    return ((uint32_t)msb_nibble << 8 | lsb) * unit;
}
static uint32_t shift_size(uint8_t s) { return s ? (64u << s) : 0; }

static void apply_db(rom_info_t *o, const romdb_entry_t *e) {
    o->source = ROM_SRC_DB;
    o->mapper = e->mapper; o->submapper = e->submapper;
    o->mirroring = ROMDB_MIRROR(e->flags);
    o->battery = !!(e->flags & ROMDB_FLAG_BATTERY);
    o->bus_conflicts = !!(e->flags & ROMDB_FLAG_BUSCONFLICT);
    o->system = e->system;
    o->prg_size = (uint32_t)e->prg_kb * 1024u;
    o->chr_size = (uint32_t)e->chr_kb * 1024u;
    o->chr_ram_size = (uint32_t)e->chrram_kb * 1024u;
    o->wram_size = (uint32_t)e->wram_kb * 1024u;
    o->sram_size = (uint32_t)e->sram_kb * 1024u;
    if (o->chr_size == 0 && o->chr_ram_size == 0) o->chr_ram_size = 8192;
}

static bool parse_header(const uint8_t *h, uint32_t len, rom_info_t *o) {
    if (len < 16 || memcmp(h, "NES\x1a", 4) != 0) return false;
    o->has_header = true;
    o->data_offset = 16;
    uint8_t f6 = h[6], f7 = h[7];
    o->trainer_size = (f6 & 0x04) ? 512 : 0;
    o->data_offset += o->trainer_size;
    o->mirroring = (f6 & 0x08) ? 2 : (f6 & 0x01) ? 1 : 0;
    o->battery = !!(f6 & 0x02);
    bool nes2 = (f7 & 0x0C) == 0x08;
    if (nes2) {
        o->source = ROM_SRC_NES20;
        o->mapper = (uint16_t)((f6 >> 4) | (f7 & 0xF0) | ((h[8] & 0x0F) << 8));
        o->submapper = h[8] >> 4;
        o->prg_size = nes2_size(h[4], h[9] & 0x0F, 16384);
        o->chr_size = nes2_size(h[5], h[9] >> 4, 8192);
        o->wram_size = shift_size(h[10] & 0x0F);
        o->sram_size = shift_size(h[10] >> 4);
        o->chr_ram_size = shift_size(h[11] & 0x0F);
        o->system = (h[12] & 3) == 1 ? 1 : 0;
        if (o->chr_size == 0 && o->chr_ram_size == 0) o->chr_ram_size = 8192;
    } else {
        o->source = ROM_SRC_INES;
        bool dirty = false; for (int i = 12; i < 16; i++) if (h[i]) dirty = true;
        o->mapper = (uint16_t)((f6 >> 4) | (dirty ? 0 : (f7 & 0xF0)));
        o->submapper = 0;
        o->prg_size = (uint32_t)h[4] * 16384u; if (o->prg_size == 0) o->prg_size = 4096u * 1024u;
        o->chr_size = (uint32_t)h[5] * 8192u;
        o->wram_size = o->battery ? 0 : 8192;
        o->sram_size = o->battery ? 8192 : 0;
        o->chr_ram_size = o->chr_size ? 0 : 8192;
        o->system = (h[9] & 1) ? 1 : 0;
    }
    return true;
}

static void heuristic(const uint8_t *img, uint32_t len, rom_info_t *o) {
    /* Headerless: assume PRG first. Common official layouts: 16K/32K NROM, 32K+8K, 128K... */
    o->source = ROM_SRC_HEURISTIC;
    o->has_header = false; o->data_offset = 0; o->mirroring = 1; o->system = 2;
    o->chr_ram_size = 0;
    if (len == 24576)       { o->prg_size = 16384;  o->chr_size = 8192;  o->mapper = 0; }
    else if (len == 40960)  { o->prg_size = 32768;  o->chr_size = 8192;  o->mapper = 0; }
    else if (len == 16384 || len == 32768) { o->prg_size = len; o->chr_size = 0; o->chr_ram_size = 8192; o->mapper = 0; }
    else if (len == 65536)  { o->prg_size = 32768;  o->chr_size = 32768; o->mapper = 3; }
    else if (len == 131072) { o->prg_size = 131072; o->chr_size = 0; o->chr_ram_size = 8192; o->mapper = 2; }
    else if (len == 262144) { o->prg_size = 131072; o->chr_size = 131072; o->mapper = 4; }
    else if ((len & 0x3FFF) == 0) { o->prg_size = len; o->chr_size = 0; o->chr_ram_size = 8192; o->mapper = 1; }
    else { o->prg_size = len & ~0x3FFFu; o->chr_size = 0; o->chr_ram_size = 8192; o->mapper = 0; }
    snprintf(o->note, sizeof o->note, "headerless: size-based guess");
    (void)img;
}

bool rom_inspect(const uint8_t *img, uint32_t len, rom_info_t *out) {
    memset(out, 0, sizeof *out);
    if (!img || len < 16384) return false;
    out->file_crc32 = fc_crc32(0, img, len);
    bool hdr = parse_header(img, len, out);
    if (!hdr) {
        /* Headerless: the DB CRC is over the raw image anyway; try that first. */
        const romdb_entry_t *e = (const romdb_entry_t *)romdb_lookup(out->file_crc32);
        if (e) { apply_db(out, e); out->has_header = false; out->data_offset = 0; out->crc32 = out->file_crc32;
                 snprintf(out->note, sizeof out->note, "headerless, DB match"); return true; }
        heuristic(img, len, out);
        out->crc32 = out->file_crc32;
        return out->prg_size != 0 && out->data_offset + out->prg_size + out->chr_size <= len;
    }
    uint32_t need = out->data_offset + out->prg_size + out->chr_size;
    if (need > len) { snprintf(out->note, sizeof out->note, "truncated image (%lu < %lu)", (unsigned long)len, (unsigned long)need); return false; }
    out->crc32 = fc_crc32(0, img + out->data_offset, out->prg_size + out->chr_size);
    const romdb_entry_t *e = (const romdb_entry_t *)romdb_lookup(out->crc32);
    if (e) {
        rom_source_t hs = out->source;
        apply_db(out, e);
        snprintf(out->note, sizeof out->note, "DB match (header was %s)", hs == ROM_SRC_NES20 ? "NES2.0" : "iNES");
    }
    return true;
}
