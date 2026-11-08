/* Host tests for the rev E portable modules: link codec, PPU address model, read confirmation, boot handshake,
 * ROM page cache, and the MMC5 paths the rev E MCUs use (A13 scanline detection, 8x16 CHR sets, split screen). */
#include "cart.h"
#include "cartload.h"
#include "mapper.h"
#include "rom.h"
#include "mappers/mmc5.h"
#include "reve/reve_link.h"
#include "reve/ppu_track.h"
#include "reve/rcommit.h"
#include "reve/bootpark.h"
#include "reve/romcache.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
static int checks, fails;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL %s:%d: ", __FILE__, __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

static void test_link(void) {
    uint16_t sym[600]; unsigned n = 0;
    n += rl_enc_write(sym + n, 0x8001, 0x5A);
    n += rl_enc_seq(sym + n, 0x11);
    n += rl_enc_ppu_addr(sym + n, 0x1FF0, true);
    n += rl_enc_ppu_data(sym + n, 0xC3);
    n += rl_enc_read(sym + n, 0x5204);
    n += rl_enc_poll(sym + n, RL_NODE_X);
    reve_load_t ld; memset(&ld, 0, sizeof ld); ld.mapper = 5; ld.prg_size = 524288; ld.chr_crc = 0xDEADBEEF;
    n += rl_enc_load_head(sym + n, sizeof ld); for (unsigned i = 0; i < sizeof ld; i++) sym[n++] = ((const uint8_t *)&ld)[i];
    n += rl_enc_bulk_addr(sym + n, 0x012345);
    uint8_t blk[200]; for (unsigned i = 0; i < sizeof blk; i++) blk[i] = (uint8_t)(i * 7);
    n += rl_enc_bulk(sym + n, blk, sizeof blk);
    n += rl_enc_cmd(sym + n, RL_C_LIVE, 1);
    rl_dec_t d; rl_dec_init(&d); rl_event_t e, ev[300]; unsigned ne = 0;
    for (unsigned i = 0; i < n; i++) if (rl_dec_feed(&d, sym[i], &e)) ev[ne++] = e;
    CHECK(ne == 9 + sizeof blk, "event count %u", ne);
    CHECK(ev[0].kind == RL_EV_WRITE && ev[0].addr == 0x8001 && ev[0].data == 0x5A, "write");
    CHECK(ev[1].kind == RL_EV_WRITE && ev[1].addr == 0x8002 && ev[1].data == 0x11, "seq write");
    CHECK(ev[2].kind == RL_EV_PPU_ADDR && ev[2].addr == 0x1FF0 && ev[2].arg == 1, "ppu addr");
    CHECK(ev[3].kind == RL_EV_PPU_DATA && ev[3].data == 0xC3, "ppu data");
    CHECK(ev[4].kind == RL_EV_READ && ev[4].addr == 0x5204, "read");
    CHECK(ev[5].kind == RL_EV_POLL && ev[5].arg == RL_NODE_X, "poll");
    CHECK(ev[6].kind == RL_EV_LOAD && ((reve_load_t *)d.load)->mapper == 5 && ((reve_load_t *)d.load)->chr_crc == 0xDEADBEEF, "load blob");
    CHECK(ev[7].kind == RL_EV_BULK_ADDR && ev[7].off == 0x012345, "bulk addr");
    bool bulk_ok = true; for (unsigned i = 0; i < sizeof blk; i++) if (ev[8 + i].kind != RL_EV_BULK_BYTE || ev[8 + i].data != blk[i] || ev[8 + i].off != 0x012345 + i) bulk_ok = false;
    CHECK(bulk_ok, "bulk bytes");
    CHECK(ev[8 + sizeof blk].kind == RL_EV_COMMAND && ev[8 + sizeof blk].data == RL_C_LIVE && ev[8 + sizeof blk].arg == 1, "command");
    CHECK(d.bad == 0, "no framing errors");
    /* lost symbol: the decoder re-aligns on the next start symbol */
    rl_dec_init(&d); uint16_t s2[8]; unsigned m = rl_enc_write(s2, 0x8000, 1); m += rl_enc_write(s2 + m, 0xA000, 2);
    unsigned got = 0; for (unsigned i = 0; i < m; i++) { if (i == 1) continue; if (rl_dec_feed(&d, s2[i], &e) && e.kind == RL_EV_WRITE) { got++; CHECK(e.addr == 0xA000 && e.data == 2, "resync write %04X", e.addr); } }
    CHECK(got == 1 && d.bad == 1, "resync after a lost symbol (got %u bad %lu)", got, (unsigned long)d.bad);
}

static void test_ppu_track(void) {
    ppu_track_t p; ppu_track_reset(&p); uint16_t va = 0;
    ppu_track_read(&p, 0x2002);
    CHECK(!ppu_track_write(&p, 0x2006, 0x21, &va) && !ppu_track_write(&p, 0x2006, 0x08, &va), "2006 writes");
    CHECK(ppu_track_write(&p, 0x2007, 0xAA, &va) && va == 0x2108, "first 2007 -> $2108 (%04X)", va);
    CHECK(ppu_track_write(&p, 0x3FFF, 0xAB, &va) && va == 0x2109, "mirror $3FFF = $2007, +1 (%04X)", va);
    ppu_track_write(&p, 0x2000, 0x04, &va);                      /* +32 */
    ppu_track_write(&p, 0x2007, 0, &va); CHECK(va == 0x210A, "%04X", va);
    ppu_track_write(&p, 0x2007, 0, &va); CHECK(va == 0x212A, "inc 32 (%04X)", va);
    ppu_track_read(&p, 0x2007);                                    /* a read also increments */
    ppu_track_write(&p, 0x2007, 0, &va); CHECK(va == 0x216A, "read increments (%04X)", va);
    /* $2005 then $2002 resets the toggle so $2006 starts with the high byte */
    ppu_track_write(&p, 0x2000, 0, &va);
    ppu_track_write(&p, 0x2005, 0x10, &va);                        /* w = 1 */
    ppu_track_read(&p, 0x200A);                                    /* $2002 mirror -> w = 0 */
    ppu_track_write(&p, 0x2006, 0x00, &va); ppu_track_write(&p, 0x2006, 0x40, &va);
    ppu_track_write(&p, 0x2007, 0, &va); CHECK(va == 0x0040, "CHR address after $2002 reset (%04X)", va);
}

static void test_rcommit(void) {
    rcommit_t r; rcommit_init(&r); uint16_t a = 0; uint32_t t = 0; int n = 0; uint16_t got[8];
    /* LDA $2002 at $C123: opcode/operands from ROM (/ROMSEL low), then $2002 read, then next opcode */
    struct { uint16_t a; int romsel, ws; uint32_t dt; } seq[] = {
        { 0x4123, 1, 0, 560 }, { 0x4124, 1, 0, 560 }, { 0x4125, 1, 0, 560 },
        { 0x2002, 0, 0, 560 },
        { 0x2006, 0, 0, 10 },                                      /* skew glitch: too short */
        { 0x4126, 1, 0, 560 },
        { 0x2006, 0, 1, 560 },                                     /* write: never a read */
        { 0x4C4C, 0, 0, 560 }, { 0x4C4D, 0, 0, 560 }, { 0x4C4E, 0, 0, 560 }, { 0x4C4C, 0, 0, 560 },
    };
    for (unsigned i = 0; i < sizeof seq / sizeof seq[0]; i++) {
        for (uint32_t k = 0; k < seq[i].dt; k += 10, t += 10)
            if (rcommit_sample(&r, seq[i].a, seq[i].romsel && k > 150, seq[i].ws && k > 150, t, 300, &a) == RC_LOW && n < 8) got[n++] = a;
    }
    CHECK(n == 4 && got[0] == 0x2002 && got[1] == 0x4C4C && got[2] == 0x4C4D && got[3] == 0x4C4E, "confirmed reads n=%d %04X %04X", n, got[0], n > 1 ? got[1] : 0);
    CHECK(rcommit_wanted(0x2002, false) && rcommit_wanted(0x3FFF, false) && !rcommit_wanted(0x2006, false) && rcommit_wanted(0x5204, true) && !rcommit_wanted(0x5204, false), "wanted filter");
}

/* Simulate the CPU parked in JMP $4C4C and the handshake into the game's reset vector. */
static void test_bootpark(void) {
    bootpark_t b; bootpark_init(&b); uint8_t v;
    CHECK(bootpark_rom(&b, 0xFFFC, 0x00) == 0x4C && bootpark_rom(&b, 0xFFFD, 0x80) == 0x4C, "parked vectors = $4C4C");
    CHECK(bootpark_low(&b, 0x4C4C, &v) && v == 0x4C, "parked loop byte");
    CHECK(!bootpark_low(&b, 0x6000, &v), "no drive elsewhere");
    /* CPU loop: opcode at 4C4C, operands 4C4D/4C4E. Arm while the CPU is reading an operand. */
    unsigned pc = 0x4C4D; bootpark_arm(&b);
    uint16_t cpu_pc = 0; int guard = 0;
    for (;;) {
        /* fetch opcode */
        uint8_t op;
        if (pc >= 0x8000) op = bootpark_rom(&b, (uint16_t)pc, 0xEA); else { if (!bootpark_low(&b, (uint16_t)pc, &op)) op = 0x4C; bootpark_commit(&b, (uint16_t)pc); }
        if (pc == 0x4C4D) { /* we started mid-instruction: this was the operand low; continue the JMP */ uint8_t hi; bootpark_low(&b, 0x4C4E, &hi); bootpark_commit(&b, 0x4C4E); pc = 0x4C4C; continue; }
        uint16_t a1 = (uint16_t)(pc + 1), a2 = (uint16_t)(pc + 2); uint8_t lo, hi;
        if (!bootpark_low(&b, a1, &lo)) lo = 0x4C;
        bootpark_commit(&b, a1);
        if (!bootpark_low(&b, a2, &hi)) hi = 0x4C;
        bootpark_commit(&b, a2);
        uint16_t t = (uint16_t)(lo | (hi << 8));
        if (op == 0x4C) pc = t;
        else if (op == 0x6C) { uint8_t vl = bootpark_rom(&b, t, 0x34), vh = bootpark_rom(&b, (uint16_t)(t + 1), 0x92); cpu_pc = (uint16_t)(vl | (vh << 8)); pc = cpu_pc; bootpark_rom(&b, cpu_pc, 0xA9); break; }
        else break;
        if (++guard > 10) break;
    }
    CHECK(cpu_pc == 0x9234, "CPU took the game's reset vector ($%04X)", cpu_pc);
    CHECK(b.state == BP_RUN, "running after the first game fetch (%u)", b.state);
}

static void test_romcache(void) {
    enum { PAGES = 64 };
    uint8_t *flash = malloc(PAGES * 8192); for (unsigned i = 0; i < PAGES * 8192; i++) flash[i] = (uint8_t)((i >> 13) * 3 + i);
    uint8_t pool[8 * 8192]; uint16_t page_slot[PAGES]; romcache_t rc;
    CHECK(romcache_init(&rc, flash, PAGES * 8192, 13, pool, sizeof pool, page_slot) == 8 && !romcache_fits(&rc), "8 slots");
    romcache_preload(&rc);
    uint8_t *tbl[4] = { flash + 9 * 8192 + 100, flash + 63 * 8192, flash + 2 * 8192, NULL };
    unsigned miss = romcache_fix(&rc, tbl, 4);
    CHECK(miss == 2 && tbl[2] >= pool && tbl[2] < pool + sizeof pool && tbl[0] == flash + 9 * 8192 + 100, "hit page 2, miss 9 and 63");
    CHECK(tbl[2][7] == flash[2 * 8192 + 7], "cached byte");
    while (romcache_service(&rc, tbl, 4)) {}
    miss = romcache_fix(&rc, tbl, 4);
    CHECK(miss == 0 && tbl[0][0] == flash[9 * 8192 + 100] && tbl[1][8191] == flash[63 * 8192 + 8191], "after service: all cached and correct");
    /* thrash: pinned pages stay valid */
    for (unsigned p = 10; p < 40; p++) { uint8_t *t2[1] = { flash + p * 8192 }; romcache_fix(&rc, t2, 1); uint8_t *live[4] = { tbl[0], tbl[1], tbl[2], t2[0] }; while (romcache_service(&rc, live, 4)) {} }
    CHECK(tbl[0][0] == flash[9 * 8192 + 100] && tbl[1][0] == flash[63 * 8192] && tbl[2][0] == flash[2 * 8192], "pinned pages survive eviction");
    free(flash);
}

static uint8_t img5[16 + 131072 + 131072];
static void load_mmc5(cart_t *c) {
    uint8_t hdr[16] = { 'N', 'E', 'S', 0x1A, 8, 16, 0x50, 0x00, 0, 0, 0, 0, 0, 0, 0, 0 };
    memcpy(img5, hdr, 16);
    for (unsigned i = 0; i < 131072; i++) img5[16 + 131072 + i] = (uint8_t)(i >> 10);   /* CHR byte = 1K page number */
    rom_info_t info; CHECK(rom_inspect(img5, sizeof img5, &info) && info.mapper == 5, "inspect mmc5");
    CHECK(cart_load_ext(c, img5 + 16, img5 + 16 + 131072, &info, NULL) == LOAD_OK, "cart_load_ext mmc5");
}
/* PPU fetch pattern of one visible scanline as rev E's PPU MCU sees it. */
static void ppu_line(cart_t *c, uint8_t *bg_nt, uint8_t *bg_pt, uint8_t *spr_pt) {
    for (int t = 2; t < 34; t++) {
        uint16_t nt = (uint16_t)(0x2000 + (t & 31));
        uint8_t v = cart_ppu_read(c, nt); if (bg_nt) bg_nt[t] = v;
        cart_ppu_read(c, (uint16_t)(0x23C0 + ((t & 31) >> 2)));
        uint8_t p = cart_ppu_read(c, (uint16_t)(v * 16)); if (bg_pt) bg_pt[t] = p;
        cart_ppu_read(c, (uint16_t)(v * 16 + 8));
    }
    for (int s = 0; s < 8; s++) { cart_ppu_read(c, 0x2000); cart_ppu_read(c, 0x2000); uint8_t p = cart_ppu_read(c, 0x1000); if (spr_pt) spr_pt[s] = p; cart_ppu_read(c, 0x1008); }
    for (int t = 0; t < 2; t++) { cart_ppu_read(c, (uint16_t)(0x2000 + t)); cart_ppu_read(c, 0x23C0); cart_ppu_read(c, 0x0000); cart_ppu_read(c, 0x0008); }
    cart_ppu_read(c, 0x2002); cart_ppu_read(c, 0x2002);            /* dots 337/339: then the next line's first read makes three */
}
static void test_mmc5(void) {
    static cart_t c; load_mmc5(&c);
    /* 8x16 sprites: set A for sprites, set B for background while rendering */
    cart_cpu_write(&c, 0x5101, 3);
    for (int i = 0; i < 8; i++) cart_cpu_write(&c, (uint16_t)(0x5120 + i), (uint8_t)(10 + i));
    for (int i = 0; i < 4; i++) cart_cpu_write(&c, (uint16_t)(0x5128 + i), (uint8_t)(40 + i));
    CHECK(c.chr_map[0][0] == 40, "8x8: last written set (B) everywhere (%u)", c.chr_map[0][0]);
    cart_cpu_write(&c, 0x2000, 0x20);
    uint8_t nt[34], pt[34], sp[8];
    ppu_line(&c, NULL, NULL, NULL); ppu_line(&c, nt, pt, sp);
    CHECK(c.s.mmc5.in_frame, "in frame after two lines");
    CHECK(pt[5] == 40 && sp[0] == 14, "8x16: BG from set B (%u), sprites $1000 from set A slot 4 (%u)", pt[5], sp[0]);
    /* scanline IRQ through U3's A13-only detector */
    static cart_t u3; load_mmc5(&u3);
    cart_cpu_write(&u3, 0x5203, 3); cart_cpu_write(&u3, 0x5204, 0x80);
    int lines = 0;
    for (int l = 0; l < 5; l++) {
        for (int t = 0; t < 32; t++) { lines += mmc5_a13_read(&u3, true); lines += mmc5_a13_read(&u3, true); mmc5_a13_read(&u3, false); mmc5_a13_read(&u3, false); }
        for (int s = 0; s < 8; s++) { mmc5_a13_read(&u3, true); mmc5_a13_read(&u3, true); mmc5_a13_read(&u3, false); mmc5_a13_read(&u3, false); }
        for (int t = 0; t < 2; t++) { mmc5_a13_read(&u3, true); mmc5_a13_read(&u3, true); mmc5_a13_read(&u3, false); mmc5_a13_read(&u3, false); }
        mmc5_a13_read(&u3, true); mmc5_a13_read(&u3, true);
    }
    CHECK(u3.s.mmc5.scanline == 3 && u3.irq_line && u3.s.mmc5.irq_pending, "A13 detector: line %u irq %u", u3.s.mmc5.scanline, u3.irq_line);
    CHECK((cart_cpu_read(&u3, 0x5204) & 0xC0) == 0xC0 && !u3.irq_line && !u3.s.mmc5.irq_pending, "$5204 read acknowledges");
    CHECK(c.mapper->peek && (c.mapper->peek(&c, 0x5204, 0) & 0x40), "peek shows in-frame without side effects");
    /* vertical split: left 4 tiles from ExRAM, CHR 4K bank $5202 */
    static cart_t d; load_mmc5(&d);
    cart_cpu_write(&d, 0x5104, 1);                                  /* ExRAM writable as ext attr... use mode 0 for split */
    cart_cpu_write(&d, 0x5104, 0);
    d.s.mmc5.in_frame = 1;                                          /* ExRAM writes in mode 0 need rendering */
    for (int i = 0; i < 1024; i++) cart_cpu_write(&d, (uint16_t)(0x5C00 + i), (uint8_t)(0x70 + (i & 7)));
    d.s.mmc5.in_frame = 0;
    cart_cpu_write(&d, 0x5101, 3); for (int i = 0; i < 8; i++) cart_cpu_write(&d, (uint16_t)(0x5120 + i), (uint8_t)i);
    cart_cpu_write(&d, 0x5200, 0x80 | 4); cart_cpu_write(&d, 0x5201, 0); cart_cpu_write(&d, 0x5202, 5);
    CHECK(d.nt_full == 1, "split needs full nametable service");
    ppu_line(&d, NULL, NULL, NULL); ppu_line(&d, nt, pt, sp);
    CHECK(nt[2] == 0x72 && nt[3] == 0x73 && pt[2] == 20 + ((0x72 * 16) >> 10), "split tiles 2..3 from ExRAM, CHR bank 5 (nt %02X pt %u)", nt[2], pt[2]);
    CHECK(pt[6] != 20 + ((0x76 * 16) >> 10) || nt[6] != 0x76, "tile 6 outside the split (nt %02X)", nt[6]);
    cart_cpu_write(&d, 0x5200, 0); CHECK(d.nt_full == 0, "split off");
}

int main(void) {
    test_link(); test_ppu_track(); test_rcommit(); test_bootpark(); test_romcache(); test_mmc5();
    printf("%d checks, %d failures\n", checks, fails);
    return fails ? 1 : 0;
}
