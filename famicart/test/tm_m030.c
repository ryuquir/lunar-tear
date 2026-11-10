/* Tests for mapper 30 (UNROM 512, src/core/mappers/m030_unrom512.c) and its header rules in rom.c. */
#include "tm_util.h"

extern const mapper_desc_t mapper_030;
static cart_t c;
static void wr(uint16_t a, uint8_t v) { cart_cpu_write(&c, a, v); }
static uint8_t rd(uint16_t a) { return cart_cpu_read(&c, a); }
/* (re)attach with a given submapper, battery bit and mirroring */
static void attach(uint8_t sub, bool battery, mirroring_t m) { c.battery = battery; c.mirroring = m; mapper_attach_desc(&c, &mapper_030, sub); c.prg_rw = tm_prg; }
/* flash command helpers as a game issues them: bank latch at $C000, flash write at $8000-$BFFF */
static void unlock(uint8_t third) { wr(0xC000, 1); wr(0x9555, 0xAA); wr(0xC000, 0); wr(0xAAAA, 0x55); wr(0xC000, 1); wr(0x9555, third); }

void tm_m030(int *checks, int *fails) {
    /* ---- plain board: sub 0, battery clear: register at $8000-$FFFF with bus conflicts ---- */
    TM_CHECK(tm_load(&c, &mapper_030, 0, 512, 0, 32, 0, 0), "30 load");
    TM_CHECK(c.chr_size == 32768 && c.chr_is_ram, "30 has 32 KB CHR-RAM (got %u)", (unsigned)c.chr_size);
    TM_CHECK(tm_prg_bank(&c, 4) == 0 && tm_prg_bank(&c, 5) == 1 && tm_prg_bank(&c, 6) == 62 && tm_prg_bank(&c, 7) == 63, "30 power-on PRG");
    TM_CHECK(c.prg_map[3] == NULL, "30 no PRG-RAM");
    TM_CHECK(c.chr_map[0] == c.chr && c.chr_map[7] == c.chr + 7 * 1024, "30 power-on CHR bank 0");
    wr(0xE005, 0xFF);                         /* ROM byte there is $3F: the register receives $3F */
    TM_CHECK(tm_prg_bank(&c, 4) == 62 && tm_prg_bank(&c, 5) == 63, "30 bus conflict masks the value (got %u)", tm_prg_bank(&c, 4));
    TM_CHECK(c.chr_map[0] == c.chr + 8192, "30 CHR bank 1 after $3F");
    TM_CHECK(tm_nt(&c, 0) == 0 && tm_nt(&c, 1) == 0 && tm_nt(&c, 2) == 1 && tm_nt(&c, 3) == 1, "30 fixed arrangement kept");
    wr(0x8000, 0xFF);                         /* ROM byte $3E (bank 31 is mapped at $8000 now) */
    TM_CHECK(tm_prg_bank(&c, 4) == 60, "30 register also at $8000 on the plain board (got %u)", tm_prg_bank(&c, 4));
    unlock(0xA0); wr(0x8123, 0x00);
    TM_CHECK(tm_prg[0x123] == 0 && tm_prg[(1u << 14) | 0x123] == 2, "30 plain board: no flash writes");

    /* ---- sub 2: bus conflicts even with the battery bit ---- */
    attach(2, true, MIRROR_H);
    wr(0xE005, 0xFF);
    TM_CHECK(tm_prg_bank(&c, 4) == 62, "30 sub 2 keeps bus conflicts");

    /* ---- sub 1: register only at $C000-$FFFF, no bus conflicts ---- */
    attach(1, false, MIRROR_V);
    wr(0x8000, 0x05);
    TM_CHECK(tm_prg_bank(&c, 4) == 0, "30 sub 1: $8000 is not the register");
    wr(0xC000, 0x45);
    TM_CHECK(tm_prg_bank(&c, 4) == 10 && tm_prg_bank(&c, 5) == 11 && tm_prg_bank(&c, 6) == 62, "30 sub 1 PRG bank 5");
    TM_CHECK(c.chr_map[0] == c.chr + 2 * 8192, "30 sub 1 CHR bank 2");
    TM_CHECK(tm_nt(&c, 1) == 1 && tm_nt(&c, 2) == 0, "30 sub 1 arrangement from the header");
    wr(0xFFFF, 0x7F);
    TM_CHECK(tm_prg_bank(&c, 4) == 62 && c.chr_map[0] == c.chr + 3 * 8192, "30 no bus conflict: full value taken");

    /* ---- one-screen board: bit 7 selects the CIRAM page ---- */
    attach(1, false, MIRROR_1A);
    TM_CHECK(tm_nt(&c, 0) == 0 && tm_nt(&c, 3) == 0, "30 one screen, page 0");
    wr(0xC000, 0x80);
    TM_CHECK(tm_nt(&c, 0) == 1 && tm_nt(&c, 1) == 1 && tm_nt(&c, 2) == 1 && tm_nt(&c, 3) == 1, "30 one screen, page 1");
    wr(0xC000, 0x01);
    TM_CHECK(tm_nt(&c, 0) == 0 && tm_nt(&c, 3) == 0 && tm_prg_bank(&c, 4) == 2, "30 one screen back to page 0");

    /* ---- four screens from the last 8 KB of CHR-RAM ---- */
    attach(1, false, MIRROR_4);
    TM_CHECK(c.nt_map[0] == c.chr + 0x6000 && c.nt_map[1] == c.chr + 0x6400 && c.nt_map[3] == c.chr + 0x6C00, "30 four-screen nametables in CHR-RAM");
    cart_ppu_write(&c, 0x2405, 0x5A);
    TM_CHECK(c.chr[0x6405] == 0x5A, "30 four-screen write lands in CHR-RAM");
    wr(0xC000, 0x60);                         /* CHR bank 3: the same RAM seen as pattern data */
    TM_CHECK(cart_ppu_read(&c, 0x0405) == 0x5A, "30 CHR bank 3 shows the nametable RAM");
    TM_CHECK(c.nt_map[0] == c.chr + 0x6000, "30 nametables do not move with the CHR bank");

    /* ---- sub 3: bit 7 switches the arrangement ---- */
    attach(3, false, MIRROR_H);
    wr(0xC000, 0x80);
    TM_CHECK(tm_nt(&c, 1) == 1 && tm_nt(&c, 2) == 0, "30 sub 3 bit 7 set: CIRAM A10 = PPU A10");
    wr(0xC000, 0x00);
    TM_CHECK(tm_nt(&c, 1) == 0 && tm_nt(&c, 2) == 1, "30 sub 3 bit 7 clear: CIRAM A10 = PPU A11");

    /* ---- self-flashable board: sub 0 with the battery bit ---- */
    TM_CHECK(tm_load(&c, &mapper_030, 0, 512, 0, 32, 0, 0), "30 reload");
    attach(0, true, MIRROR_H);
    wr(0x8000, 0x03);
    TM_CHECK(tm_prg_bank(&c, 4) == 0, "30 flashable: $8000 is not the register");
    wr(0xC000, 3); wr(0x8123, 0x00);          /* no unlock: nothing happens */
    TM_CHECK(tm_prg[(3u << 14) | 0x123] == 6, "30 flash write needs the unlock sequence");
    unlock(0xA0); wr(0xC000, 3); wr(0x8123, 0x02);
    TM_CHECK(tm_prg[(3u << 14) | 0x123] == 0x02, "30 byte program (got %02X)", tm_prg[(3u << 14) | 0x123]);
    TM_CHECK(c.s.m030.prg_dirty == 1, "30 program sets prg_dirty");
    TM_CHECK(rd(0x8123) == 0x02, "30 programmed byte reads back");
    unlock(0xA0); wr(0xC000, 3); wr(0x8123, 0xFD);
    TM_CHECK(tm_prg[(3u << 14) | 0x123] == 0x00, "30 programming only clears bits");
    wr(0x8124, 0x00);
    TM_CHECK(tm_prg[(3u << 14) | 0x124] == 6, "30 one byte per program command");
    /* sector erase: 4 KB at bank 3, $9000 */
    unlock(0x80); wr(0xC000, 1); wr(0x9555, 0xAA); wr(0xC000, 0); wr(0xAAAA, 0x55); wr(0xC000, 3); wr(0x9000, 0x30);
    TM_CHECK(tm_prg[0xD000] == 0xFF && tm_prg[0xDFFF] == 0xFF, "30 sector erase fills 4 KB with $FF");
    TM_CHECK(tm_prg[0xCFFF] == 6 && tm_prg[0xE000] == 7 && tm_prg[(3u << 14) | 0x123] == 0x00, "30 sector erase leaves the neighbours");
    unlock(0xA0); wr(0xC000, 3); wr(0x9010, 0x12);
    TM_CHECK(tm_prg[0xD010] == 0x12, "30 program after erase");
    /* a broken erase sequence is dropped */
    unlock(0x80); wr(0xC000, 1); wr(0x9555, 0x00); wr(0xC000, 3); wr(0xA000, 0x30);
    TM_CHECK(tm_prg[0xE000] == 7, "30 broken erase sequence does nothing");
    /* software ID */
    unlock(0x90);
    TM_CHECK(rd(0x8000) == 0xBF && rd(0x8001) == 0xB7, "30 software ID bytes (got %02X %02X)", rd(0x8000), rd(0x8001));
    wr(0xC000, 5);
    TM_CHECK(rd(0x8000) == 0xBF, "30 ID mode survives a bank write");
    wr(0x8000, 0xF0);
    TM_CHECK(tm_prg_bank(&c, 4) == 10 && tm_prg_bank(&c, 6) == 62, "30 ID exit restores the banks (got %u)", tm_prg_bank(&c, 4));
    /* chip erase */
    unlock(0x80); wr(0xC000, 1); wr(0x9555, 0xAA); wr(0xC000, 0); wr(0xAAAA, 0x55); wr(0xC000, 1); wr(0x9555, 0x10);
    TM_CHECK(tm_prg[0] == 0xFF && tm_prg[512 * 1024 - 1] == 0xFF, "30 chip erase");
    /* without a writable image the commands are accepted and ignored */
    TM_CHECK(tm_load(&c, &mapper_030, 0, 256, 0, 32, 0, 0), "30 reload 256K");
    c.battery = true; mapper_attach_desc(&c, &mapper_030, 0);
    TM_CHECK(c.prg_rw == NULL, "30 prg_rw is the platform's choice");
    unlock(0xA0); wr(0xC000, 3); wr(0x8123, 0x00);
    TM_CHECK(tm_prg[(3u << 14) | 0x123] == 6, "30 read-only image is not touched");
    TM_CHECK(tm_prg_bank(&c, 6) == 30 && tm_prg_bank(&c, 7) == 31, "30 256K: last bank fixed");
    wr(0xC000, 0x1F);
    TM_CHECK(tm_prg_bank(&c, 4) == 30, "30 256K: bank number wraps (got %u)", tm_prg_bank(&c, 4));

    /* ---- header rules ---- */
    uint8_t h[16] = { 'N', 'E', 'S', 0x1A, 32, 0, 0xE0, 0x10, 0, 0, 0, 0, 0, 0, 0, 0 };   /* mapper 30, 512K PRG */
    rom_info_t ri;
    TM_CHECK(rom_inspect_header(h, 512 * 1024, 0x12345678, &ri) && ri.mapper == 30, "30 header mapper");
    TM_CHECK(ri.chr_ram_size == 32768 && ri.wram_size == 0 && ri.sram_size == 0 && ri.mirroring == 0, "30 iNES defaults: 32K CHR-RAM, no PRG-RAM");
    h[6] = 0xE8; TM_CHECK(rom_inspect_header(h, 512 * 1024, 0x12345678, &ri) && ri.mirroring == 3, "30 header bit 3 alone = one screen");
    h[6] = 0xE9; TM_CHECK(rom_inspect_header(h, 512 * 1024, 0x12345678, &ri) && ri.mirroring == 2, "30 header bits 3+0 = four screens");
    h[6] = 0xE3; TM_CHECK(rom_inspect_header(h, 512 * 1024, 0x12345678, &ri) && ri.battery && ri.sram_size == 0 && ri.mirroring == 1, "30 battery bit = flashable, no save RAM");
    h[6] = 0xE0; h[7] = 0x18; h[8] = 0x10; h[11] = 0x09;   /* NES 2.0, submapper 1, CHR-RAM 64 << 9 = 32 KB */
    TM_CHECK(rom_inspect_header(h, 512 * 1024, 0x12345678, &ri) && ri.mapper == 30 && ri.submapper == 1 && ri.chr_ram_size == 32768, "30 NES 2.0 header");
}
