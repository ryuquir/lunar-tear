/* Cartridge RAM on the licensed boards whose RAM sits behind mapper logic: MMC5 (PRG-RAM chip select, protect,
 * ExRAM), VRC2 / VRC4, Namco 163 (write protect per 2 KB), Taito X1-005 / X1-017; then the Sunsoft-4 sub-cartridge
 * board and bus conflicts by submapper. Expected behaviour is the nesdev wiki's (MMC5, INES_Mapper_019, Taito_X1-005,
 * Taito_X1-017, VRC2_and_VRC4, INES_Mapper_068). These carts are loaded through the registry (not tm_load), so that
 * the loader's own decisions (RAM sizes, bus conflicts) are part of the test. Written from the 2026-11 coverage
 * review: every block failed before the fixes of the same commit. */
#include "tm_util.h"

static cart_t c;
static void wr(uint16_t a, uint8_t v) { cart_cpu_write(&c, a, v); }
static uint8_t rd0(uint16_t a) { return cart_cpu_read(&c, a); }
/* read-back that cannot pass by luck: put a ROM byte on the bus first, so an unmapped address does not return the
 * value that was just written (open bus). The last PRG bank of the 128 KB test images reads $0F at $E000. */
static uint8_t rd(uint16_t a) { cart_cpu_read(&c, 0xE000); return cart_cpu_read(&c, a); }
/* what an unmapped address returns right after reading `from`: that byte (open bus) */
static bool open_bus_at(uint16_t a, uint16_t from) { uint8_t x = rd0(from); return rd0(a) == x; }

static bool load(uint16_t mapper, uint8_t sub, uint32_t prg_kb, uint32_t chr_kb, uint32_t wram_kb, uint32_t sram_kb, bool battery) {
    free(tm_prg); free(tm_chr);
    tm_prg = malloc(prg_kb * 1024 + 1); tm_chr = malloc(chr_kb * 1024 + 1024);
    for (uint32_t i = 0; i < prg_kb * 1024; i++) { uint32_t b = i >> 13; tm_prg[i] = (i & 0x1FFF) == 1 ? (uint8_t)(b >> 8) : (uint8_t)b; }
    for (uint32_t i = 0; i < chr_kb * 1024; i++) { uint32_t b = i >> 10; tm_chr[i] = (i & 0x3FF) == 1 ? (uint8_t)(b >> 8) : (uint8_t)b; }
    rom_info_t info; memset(&info, 0, sizeof info);
    info.source = ROM_SRC_DB; info.mapper = mapper; info.submapper = sub; info.battery = battery;
    info.prg_size = prg_kb * 1024; info.chr_size = chr_kb * 1024; info.chr_ram_size = chr_kb ? 0 : 8192;
    info.wram_size = wram_kb * 1024; info.sram_size = sram_kb * 1024;
    return cart_load_ext(&c, tm_prg, chr_kb ? tm_chr : NULL, &info, NULL) == LOAD_OK;
}
static void mmc5_ram_on(void) { wr(0x5102, 2); wr(0x5103, 1); }

void tm_ram(int *checks, int *fails) {
    /* ================= MMC5, EKROM: one 8 KB chip ================= */
    TM_CHECK(load(5, 0, 128, 128, 0, 8, true), "mmc5 8K load");
    wr(0x5113, 0);
    wr(0x6010, 0x11);
    TM_CHECK(rd(0x6010) == 0x00, "mmc5: RAM is write-protected until $5102=2 and $5103=1 (got %02X)", rd(0x6010));
    mmc5_ram_on();
    wr(0x6010, 0x99);
    TM_CHECK(rd(0x6010) == 0x99, "mmc5: PRG-RAM at $6000 stores a write (got %02X)", rd(0x6010));
    wr(0x5104, 2);                                   /* ExRAM as plain RAM */
    wr(0x5C10, 0x77);
    TM_CHECK(rd(0x5C10) == 0x77, "mmc5: ExRAM mode 2 read/write");
    wr(0x6010, 0x55);
    TM_CHECK(rd(0x5C10) == 0x77, "mmc5: a PRG-RAM write must not touch ExRAM (ExRAM[$10] = %02X)", rd(0x5C10));
    TM_CHECK(rd(0x6010) == 0x55, "mmc5: second PRG-RAM write stored");
    wr(0x8010, 0x33);                                /* ROM is mapped at $8000 */
    TM_CHECK(rd(0x5C10) == 0x77, "mmc5: a write to ROM must not touch ExRAM (ExRAM[$10] = %02X)", rd(0x5C10));
    wr(0x5113, 1);
    TM_CHECK(rd(0x6010) == 0x55, "mmc5 8K: bank bits 0-1 do not matter with one 8 KB chip");
    wr(0x5113, 4);                                   /* bit 2: the second chip, which this board does not have */
    TM_CHECK(open_bus_at(0x6010, 0xE000), "mmc5 8K: bank 4 is open bus, not RAM and not ExRAM (got %02X)", rd(0x6010));
    wr(0x6010, 0xAB);
    wr(0x5113, 0);
    TM_CHECK(rd(0x6010) == 0x55, "mmc5 8K: a write with bank 4 selected goes nowhere");
    wr(0x5102, 0);
    wr(0x6010, 0xEE);
    TM_CHECK(rd(0x6010) == 0x55, "mmc5: protect again blocks writes");
    mmc5_ram_on();
    /* RAM banked into $8000 (mode 3, register bit 7 clear) */
    wr(0x5100, 3); wr(0x5114, 0x00);
    TM_CHECK(rd(0x8010) == 0x55, "mmc5: the same RAM page appears at $8000");
    wr(0x8011, 0xA5);
    wr(0x5114, 0x80);                                /* back to ROM bank 0 */
    TM_CHECK(rd(0x6011) == 0xA5, "mmc5: write through $8000 landed in the RAM page");
    wr(0x5114, 0x04);
    TM_CHECK(open_bus_at(0x8010, 0xE000), "mmc5 8K: RAM bank 4 at $8000 is open bus");

    /* ================= MMC5, ETROM: two 8 KB chips ================= */
    TM_CHECK(load(5, 0, 128, 128, 8, 8, true), "mmc5 16K load");
    TM_CHECK(c.wram_size == 16384, "mmc5 16K: two chips (%u bytes)", (unsigned)c.wram_size);
    mmc5_ram_on();
    wr(0x5113, 0); wr(0x6000, 0xA0);
    wr(0x5113, 4); wr(0x6000, 0xB4);
    wr(0x5113, 0); TM_CHECK(rd(0x6000) == 0xA0, "mmc5 16K: bank 0 = first chip");
    wr(0x5113, 1); TM_CHECK(rd(0x6000) == 0xA0, "mmc5 16K: bank 1 mirrors the first chip (got %02X)", rd(0x6000));
    wr(0x5113, 3); TM_CHECK(rd(0x6000) == 0xA0, "mmc5 16K: bank 3 mirrors the first chip");
    wr(0x5113, 4); TM_CHECK(rd(0x6000) == 0xB4, "mmc5 16K: bank 4 = second chip (got %02X)", rd(0x6000));
    wr(0x5113, 7); TM_CHECK(rd(0x6000) == 0xB4, "mmc5 16K: bank 7 mirrors the second chip");
    wr(0x5100, 3); wr(0x5115, 0x05);                 /* second chip at $A000 */
    TM_CHECK(rd(0xA000) == 0xB4, "mmc5 16K: second chip banked at $A000");

    /* ================= MMC5, EWROM: one 32 KB chip ================= */
    TM_CHECK(load(5, 0, 128, 128, 0, 32, true), "mmc5 32K load");
    mmc5_ram_on();
    for (unsigned b = 0; b < 4; b++) { wr(0x5113, (uint8_t)b); wr(0x6000, (uint8_t)(0xC0 + b)); }
    for (unsigned b = 0; b < 4; b++) { wr(0x5113, (uint8_t)b); TM_CHECK(rd(0x6000) == 0xC0 + b, "mmc5 32K: page %u is its own page", b); }
    wr(0x5113, 5);
    TM_CHECK(open_bus_at(0x6000, 0xE000), "mmc5 32K: banks 4-7 are open bus");

    /* ================= MMC5: $5130 is taken when a CHR register is written ================= */
    TM_CHECK(load(5, 0, 128, 1024, 0, 8, false), "mmc5 1M CHR load");
    wr(0x5101, 3);
    wr(0x5130, 1); wr(0x5120, 0x10);
    wr(0x5130, 0); wr(0x5121, 0x20);
    TM_CHECK(tm_chr_bank(&c, 0) == 0x110, "mmc5: $5120 keeps the upper bits it was written with (got %03X)", tm_chr_bank(&c, 0));
    TM_CHECK(tm_chr_bank(&c, 1) == 0x020, "mmc5: $5121 written with upper bits 0 (got %03X)", tm_chr_bank(&c, 1));
    wr(0x5130, 2); wr(0x5128, 0x05);                 /* set B, written last: used for all fetches outside 8x16 rendering */
    TM_CHECK(tm_chr_bank(&c, 0) == 0x205 && tm_chr_bank(&c, 4) == 0x205, "mmc5: set B register with upper bits 2 (got %03X)", tm_chr_bank(&c, 0));
    wr(0x5130, 0); wr(0x5122, 0x07);                 /* back to set A: slot 0 still carries its own upper bits */
    TM_CHECK(tm_chr_bank(&c, 0) == 0x110 && tm_chr_bank(&c, 2) == 0x007, "mmc5: set A values survive (got %03X %03X)", tm_chr_bank(&c, 0), tm_chr_bank(&c, 2));

    /* ================= MMC5: nametable source 2 ================= */
    wr(0x5106, 0x42); wr(0x5107, 1);                 /* fill tile / colour */
    wr(0x5105, 0xAA);                                /* all four nametables from ExRAM */
    wr(0x5104, 2); wr(0x5C00, 0x99);
    TM_CHECK(cart_ppu_read(&c, 0x2000) == 0x00 && cart_ppu_read(&c, 0x23C0) == 0x00, "mmc5: ExRAM nametable reads zeros in ExRAM mode 2 (got %02X %02X)", cart_ppu_read(&c, 0x2000), cart_ppu_read(&c, 0x23C0));
    wr(0x5104, 3);
    TM_CHECK(cart_ppu_read(&c, 0x2000) == 0x00, "mmc5: ... and in mode 3");
    wr(0x5104, 0);
    TM_CHECK(cart_ppu_read(&c, 0x2000) == 0x99, "mmc5: ExRAM is the nametable in mode 0");
    wr(0x5105, 0xFF);
    TM_CHECK(cart_ppu_read(&c, 0x2000) == 0x42 && cart_ppu_read(&c, 0x23C0) == 0x55, "mmc5: fill mode still works");

    /* ================= VRC2 / VRC4 with RAM ================= */
    static const uint16_t vrc[] = { 21, 22, 23, 25 };
    for (unsigned i = 0; i < 4; i++) {
        TM_CHECK(load(vrc[i], 0, 128, 128, 0, 8, true), "vrc %u load", vrc[i]);
        wr(0x6123, 0x5A); wr(0x7FFF, 0xC3);
        TM_CHECK(rd(0x6123) == 0x5A && rd(0x7FFF) == 0xC3, "mapper %u: RAM at $6000-$7FFF stores writes (got %02X %02X)", vrc[i], rd(0x6123), rd(0x7FFF));
    }
    /* VRC2 without RAM: one latch bit at $6000-$6FFF, the rest open bus */
    TM_CHECK(load(22, 0, 128, 128, 0, 0, false), "vrc2a no-RAM load");
    TM_CHECK(c.prg_map[3] == NULL, "vrc2a: no RAM mapped when the cart has none");
    wr(0x6000, 0x01);                                /* rd() puts the ROM byte of the last bank ($0F) on the bus first */
    TM_CHECK(rd(0x6100) == (0x0E | 1), "vrc2 latch reads back in bit 0, rest open bus (got %02X)", rd(0x6100));
    wr(0x6000, 0x00);
    TM_CHECK(rd(0x6000) == 0x0E, "vrc2 latch cleared (got %02X)", rd(0x6000));
    TM_CHECK(open_bus_at(0x7000, 0xE000), "vrc2: $7000-$7FFF is open bus");

    /* ================= Namco 163: write protect of the external RAM ================= */
    TM_CHECK(load(19, 0, 128, 128, 0, 8, true), "n163 8K load");
    wr(0x6000, 0x12);
    TM_CHECK(rd(0x6000) == 0x00, "n163: RAM is protected until $F800 carries the key (got %02X)", rd(0x6000));
    wr(0xF800, 0x40);
    wr(0x6000, 0x12); wr(0x6800, 0x23); wr(0x7000, 0x34); wr(0x7FFF, 0x45);
    TM_CHECK(rd(0x6000) == 0x12 && rd(0x6800) == 0x23 && rd(0x7000) == 0x34 && rd(0x7FFF) == 0x45, "n163: $F800=$40 enables all four 2 KB windows (got %02X %02X %02X %02X)", rd(0x6000), rd(0x6800), rd(0x7000), rd(0x7FFF));
    wr(0xF800, 0x41);                                /* bit 0 protects $6000-$67FF */
    wr(0x6000, 0x56); wr(0x6800, 0x67);
    TM_CHECK(rd(0x6000) == 0x12 && rd(0x6800) == 0x67, "n163: bit 0 protects only $6000-$67FF (got %02X %02X)", rd(0x6000), rd(0x6800));
    wr(0xF800, 0x48);                                /* bit 3 protects $7800-$7FFF */
    wr(0x7FFF, 0x78); wr(0x7000, 0x89);
    TM_CHECK(rd(0x7FFF) == 0x45 && rd(0x7000) == 0x89, "n163: bit 3 protects only $7800-$7FFF (got %02X %02X)", rd(0x7FFF), rd(0x7000));
    static const uint8_t nokey[] = { 0x00, 0x80, 0x30, 0x50, 0xC0 };
    for (unsigned i = 0; i < sizeof nokey; i++) {
        wr(0xF800, nokey[i]); wr(0x6800, (uint8_t)(0x90 + i));
        TM_CHECK(rd(0x6800) == 0x67, "n163: $F800=$%02X (upper nibble not 4) protects everything (got %02X)", nokey[i], rd(0x6800));
    }
    /* the same write also sets the chip-RAM address (bit 7 = auto-increment) */
    wr(0xF800, 0x85); wr(0x4800, 0xD1); wr(0x4800, 0xD2);
    TM_CHECK(c.exram && c.exram[5] == 0xD1 && c.exram[6] == 0xD2, "n163: chip RAM port with auto-increment");
    wr(0xF800, 0x05);
    TM_CHECK(rd0(0x4800) == 0xD1 && rd0(0x4800) == 0xD1, "n163: chip RAM read without auto-increment");
    /* battery but no external RAM in the database: the game saves in the 128 bytes of chip RAM */
    TM_CHECK(load(19, 0, 128, 128, 0, 0, true), "n163 battery / no WRAM load");
    TM_CHECK(c.wram == NULL && c.prg_map[3] == NULL, "n163: no external RAM invented for a chip-RAM-only cart (%u bytes)", (unsigned)c.wram_size);
    TM_CHECK(c.exram != NULL, "n163: chip RAM present");
    TM_CHECK(open_bus_at(0x6000, 0xE000), "n163: $6000 is open bus without external RAM");
    /* a header that says nothing (no battery): keep the generous 8 KB */
    TM_CHECK(load(19, 0, 128, 128, 0, 0, false), "n163 no-info load");
    TM_CHECK(c.wram_size == 8192, "n163: 8 KB default kept when the database gives no hint");

    /* ================= Taito X1-005: 128 bytes at $7F00, mirrored, behind the $A3 key ================= */
    static const uint16_t x1005[] = { 80, 207 };
    for (unsigned i = 0; i < 2; i++) {
        unsigned m = x1005[i];
        TM_CHECK(load((uint16_t)m, 0, 128, 128, 0, 0, true), "x1-005 (%u) load", m);
        wr(0x7EF8, 0xA3);
        wr(0x7F10, 0xC3);
        TM_CHECK(rd(0x7F10) == 0xC3, "mapper %u: 128-byte RAM stores a write (got %02X)", m, rd(0x7F10));
        TM_CHECK(rd(0x7F90) == 0xC3, "mapper %u: $7F80-$7FFF mirrors $7F00-$7F7F (got %02X)", m, rd(0x7F90));
        wr(0x7FFF, 0x3C);
        TM_CHECK(rd(0x7F7F) == 0x3C, "mapper %u: write through the mirror", m);
        wr(0x7EF8, 0x00);
        wr(0x7F10, 0x11);
        TM_CHECK(open_bus_at(0x7F10, 0xE000), "mapper %u: RAM disabled reads open bus", m);
        wr(0x7EF9, 0xA3);                            /* $7EF9 mirrors $7EF8 */
        TM_CHECK(rd(0x7F10) == 0xC3, "mapper %u: a write while disabled was ignored (got %02X)", m, rd(0x7F10));
    }

    /* ================= Taito X1-017: 5 KB in three windows with their own keys ================= */
    TM_CHECK(load(82, 0, 128, 128, 0, 8, true), "x1-017 load");
    wr(0x6000, 0x11); wr(0x6800, 0x22); wr(0x7000, 0x33);
    wr(0x7EF7, 0xCA); wr(0x7EF8, 0x69); wr(0x7EF9, 0x84);
    TM_CHECK(rd(0x6000) == 0x00 && rd(0x6800) == 0x00 && rd(0x7000) == 0x00, "x1-017: writes before the keys were ignored");
    wr(0x6000, 0x11); wr(0x67FF, 0x12); wr(0x6800, 0x22); wr(0x73FF, 0x33);
    TM_CHECK(rd(0x6000) == 0x11 && rd(0x67FF) == 0x12 && rd(0x6800) == 0x22 && rd(0x73FF) == 0x33, "x1-017: all three windows store writes");
    wr(0x7EF8, 0x00);
    wr(0x6800, 0x99);
    wr(0x7EF8, 0x69);
    TM_CHECK(rd(0x6800) == 0x22 && rd(0x6000) == 0x11, "x1-017: one window disabled alone");
    /* the database may give no RAM size: the 5 KB are inside the mapper chip and must exist anyway */
    TM_CHECK(load(82, 0, 128, 128, 0, 0, true), "x1-017 no-size load");
    wr(0x7EF7, 0xCA); wr(0x6001, 0x5E);
    TM_CHECK(rd(0x6001) == 0x5E, "x1-017: RAM exists without a database size (got %02X)", rd(0x6001));

    /* ================= Sunsoft-4 submapper 1: Nantettatte!! Baseball with its sub-cartridge ================= */
    TM_CHECK(load(68, 1, 144, 128, 0, 0, false), "sunsoft-4 sub 1 load (128 KB + 16 KB)");
    TM_CHECK(tm_prg_bank(&c, 6) == 14 && tm_prg_bank(&c, 7) == 15, "s4 sub 1: $C000 is the last INTERNAL bank (got %u)", tm_prg_bank(&c, 6));
    wr(0xF000, 0x0B);                                /* R = 1: internal bank 3 */
    TM_CHECK(tm_prg_bank(&c, 4) == 6 && tm_prg_bank(&c, 5) == 7, "s4 sub 1: internal bank 3 at $8000 (got %u)", tm_prg_bank(&c, 4));
    wr(0xF000, 0x00);                                /* R = 0: sub-cartridge, watchdog not running */
    TM_CHECK(c.prg_map[4] == NULL && c.prg_map[5] == NULL, "s4 sub 1: sub-cartridge is open bus until its watchdog is started");
    TM_CHECK(tm_prg_bank(&c, 6) == 14, "s4 sub 1: fixed bank unaffected");
    wr(0x6000, 0x00);                                /* RAM disabled: this restarts the watchdog */
    TM_CHECK(tm_prg_bank(&c, 4) == 16 && tm_prg_bank(&c, 5) == 17, "s4 sub 1: sub-cartridge ROM at $8000 (got %u)", tm_prg_bank(&c, 4));
    wr(0xF000, 0x05);                                /* still R = 0: the 16 KB sub-cartridge ROM is mirrored */
    TM_CHECK(tm_prg_bank(&c, 4) == 16, "s4 sub 1: sub-cartridge ROM mirrored for every bank number");
    for (unsigned i = 0; i < 107519; i++) cart_cpu_cycle(&c);
    TM_CHECK(tm_prg_bank(&c, 4) == 16, "s4 sub 1: watchdog still running after 107,519 cycles");
    cart_cpu_cycle(&c);
    TM_CHECK(c.prg_map[4] == NULL, "s4 sub 1: watchdog expired: open bus again");
    wr(0x7FFF, 0x00);
    TM_CHECK(tm_prg_bank(&c, 4) == 16, "s4 sub 1: any $6000-$7FFF write restarts it");
    wr(0xF000, 0x1A);                                /* E = 1, R = 1, bank 2 */
    TM_CHECK(tm_prg_bank(&c, 4) == 4, "s4 sub 1: back to internal bank 2");
    TM_CHECK(load(68, 1, 128, 128, 0, 0, false), "sunsoft-4 sub 1 without the sub-cartridge");
    wr(0xF000, 0x00); wr(0x6000, 0x00);
    TM_CHECK(c.prg_map[4] == NULL, "s4 sub 1: no sub-cartridge in the image: open bus");
    TM_CHECK(load(68, 0, 128, 128, 0, 0, false), "sunsoft-4 sub 0 load");
    TM_CHECK(tm_prg_bank(&c, 6) == 14 && !c.has_cpu_cycle_hook, "s4 sub 0: last bank fixed, no cycle hook");
    wr(0xF000, 0x05);
    TM_CHECK(tm_prg_bank(&c, 4) == 10, "s4 sub 0: 4-bit bank number (got %u)", tm_prg_bank(&c, 4));

    /* ================= bus conflicts follow the NES 2.0 submapper on mappers 2 / 3 / 7 ================= */
    TM_CHECK(load(2, 2, 128, 0, 0, 0, false), "uxrom sub 2 load");
    wr(0x8000, 0x03);                                /* the ROM byte at $8000 is $00 (bank 0) */
    TM_CHECK(tm_prg_bank(&c, 4) == 0, "uxrom sub 2: the ROM byte wins the bus conflict (got %u)", tm_prg_bank(&c, 4));
    wr(0xE000, 0x03);                                /* ROM byte $0F */
    TM_CHECK(tm_prg_bank(&c, 4) == 6, "uxrom sub 2: $03 AND $0F = bank 3");
    TM_CHECK(load(2, 1, 128, 0, 0, 0, false), "uxrom sub 1 load");
    wr(0x8000, 0x03);
    TM_CHECK(tm_prg_bank(&c, 4) == 6, "uxrom sub 1: no bus conflict (got %u)", tm_prg_bank(&c, 4));
    TM_CHECK(load(3, 2, 32, 32, 0, 0, false), "cnrom sub 2 load");
    wr(0x8000, 0x03);
    TM_CHECK(tm_chr_bank(&c, 0) == 0, "cnrom sub 2: the ROM byte wins (got %u)", tm_chr_bank(&c, 0));
    TM_CHECK(load(3, 1, 32, 32, 0, 0, false), "cnrom sub 1 load");
    wr(0x8000, 0x03);
    TM_CHECK(tm_chr_bank(&c, 0) == 24, "cnrom sub 1: no bus conflict (got %u)", tm_chr_bank(&c, 0));
}
