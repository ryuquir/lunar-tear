/* Tests for src/core/mappers/m_port_mmc3x.c (37, 47, 176, 189, 238, 262, 361, 366). */
#include "tm_util.h"

extern const mapper_desc_t mapper_037, mapper_047, mapper_176, mapper_189, mapper_238, mapper_262, mapper_361, mapper_366;
static cart_t c;

static void wr(uint16_t a, uint8_t v) { cart_cpu_write(&c, a, v); }
static void mmc3r(uint8_t idx, uint8_t v) { wr(0x8000, idx); wr(0x8001, v); }
static void prg8(uint32_t *b) { for (unsigned i = 0; i < 4; i++) b[i] = tm_prg_bank(&c, 4 + i); }
static bool prg_is(uint32_t a, uint32_t b, uint32_t d, uint32_t e) { uint32_t p[4]; prg8(p); return p[0] == a && p[1] == b && p[2] == d && p[3] == e; }
/* one scanline worth of A12: low for a while, then a rising edge */
static void a12_pulse(void) { for (int i = 0; i < 8; i++) cart_ppu_read(&c, 0x0000); cart_ppu_read(&c, 0x1000); cart_ppu_read(&c, 0x1000); }

static void irq_check(int *checks, int *fails, const char *name) {
    wr(0xC000, 2); wr(0xC001, 0); wr(0xE001, 0);
    a12_pulse();                               /* reload -> 2 */
    TM_CHECK(!c.irq_line, "%s irq not yet (reload)", name);
    a12_pulse();                               /* 1 */
    TM_CHECK(!c.irq_line, "%s irq not yet (1)", name);
    a12_pulse();                               /* 0 -> fire */
    TM_CHECK(c.irq_line, "%s irq fires at 0", name);
    wr(0xE000, 0);
    TM_CHECK(!c.irq_line, "%s irq ack", name);
}

/* ------------------------------------------------------------------------------------------------ */
static void t_176(int *checks, int *fails) {
    /* submapper 0, 1 MiB PRG, 512 KiB CHR */
    TM_CHECK(tm_load(&c, &mapper_176, 0, 1024, 512, 0, 8, 0), "176 load");
    TM_CHECK(prg_is(0, 1, 0x3E, 0x3F), "176 power-on PRG (mode 0, 512K)");
    TM_CHECK(tm_chr_bank(&c, 0) == 0 && tm_chr_bank(&c, 1) == 1 && tm_chr_bank(&c, 2) == 2 && tm_chr_bank(&c, 4) == 4 && tm_chr_bank(&c, 7) == 7, "176 power-on CHR");
    TM_CHECK(tm_nt(&c, 1) == 0 && tm_nt(&c, 2) == 1, "176 power-on header mirroring H");
    TM_CHECK(c.prg_map[3] != NULL, "176 WRAM mapped");
    /* MMC3 inner banks */
    mmc3r(6, 0x05); mmc3r(7, 0x46);
    TM_CHECK(prg_is(5, 6, 0x3E, 0x3F), "176 MMC3 PRG masked to 6 bits (got %u %u)", tm_prg_bank(&c, 4), tm_prg_bank(&c, 5));
    wr(0x8000, 0x40);
    TM_CHECK(prg_is(0x3E, 6, 5, 0x3F), "176 PRG inversion");
    wr(0x8000, 0x00);
    mmc3r(0, 0x10); mmc3r(2, 0x33);
    TM_CHECK(tm_chr_bank(&c, 0) == 0x10 && tm_chr_bank(&c, 1) == 0x11 && tm_chr_bank(&c, 4) == 0x33, "176 MMC3 CHR");
    /* PRG base, mode 0: A19-A20 from $5xx1 bits 5-6 */
    wr(0x5011, 0x20);
    TM_CHECK(prg_is(0x45, 0x46, 0x7E, 0x7F), "176 PRG base mode 0 (got %u)", tm_prg_bank(&c, 4));
    wr(0x5001, 0x00);   /* A4 clear: solder pad 0 ignores it */
    TM_CHECK(tm_prg_bank(&c, 4) == 0x45, "176 pad 0 needs A4");
    wr(0x5FF1, 0x00);
    TM_CHECK(tm_prg_bank(&c, 4) == 5, "176 $5FF1 mirror");
    /* mode 1 (256K), mode 2 (128K) */
    wr(0x5011, 0x10); wr(0x5010, 0x01);
    TM_CHECK(prg_is(0x25, 0x26, 0x3E, 0x3F), "176 mode 1 (got %u %u %u %u)", tm_prg_bank(&c, 4), tm_prg_bank(&c, 5), tm_prg_bank(&c, 6), tm_prg_bank(&c, 7));
    wr(0x5011, 0x08); wr(0x5010, 0x02);
    TM_CHECK(prg_is(0x15, 0x16, 0x1E, 0x1F), "176 mode 2 (got %u)", tm_prg_bank(&c, 4));
    /* NROM-128, NROM-256 */
    wr(0x5011, 0x0B); wr(0x5010, 0x03);
    TM_CHECK(prg_is(0x16, 0x17, 0x16, 0x17), "176 NROM-128");
    wr(0x5010, 0x04);
    TM_CHECK(prg_is(0x14, 0x15, 0x16, 0x17), "176 NROM-256");
    /* UNROM: latch sets inner 16K, $C000 inner 7, MMC3 not touched */
    wr(0x5011, 0x08); wr(0x5010, 0x05);
    TM_CHECK(prg_is(0x10, 0x11, 0x1E, 0x1F), "176 UNROM power latch 0 (got %u)", tm_prg_bank(&c, 4));
    wr(0xE001, 0x03);
    TM_CHECK(prg_is(0x16, 0x17, 0x1E, 0x1F), "176 UNROM latch 3");
    TM_CHECK(c.s.mmc3.irq_enable == 0, "176 UNROM latch write kept from MMC3");
    wr(0x5010, 0x00); wr(0x5011, 0x00);
    /* CHR base: MMC3 256K and 128K */
    wr(0x5012, 0x20);
    TM_CHECK(tm_chr_bank(&c, 0) == 0x110 && tm_chr_bank(&c, 4) == 0x133, "176 CHR base 256K (got %x)", tm_chr_bank(&c, 0));
    mmc3r(2, 0xB3);
    wr(0x5010, 0x10); wr(0x5012, 0x10);
    TM_CHECK(tm_chr_bank(&c, 4) == 0xB3, "176 CHR base 128K (got %x)", tm_chr_bank(&c, 4));
    wr(0x5012, 0x00);
    TM_CHECK(tm_chr_bank(&c, 4) == 0x33, "176 CHR 128K masks inner bit 7");
    /* NROM CHR (bit 6) */
    wr(0x5010, 0x40); wr(0x5012, 0x05);
    TM_CHECK(tm_chr_bank(&c, 0) == 40 && tm_chr_bank(&c, 7) == 47, "176 8K CHR from base");
    /* CHR-RAM select (bit 5) on a CHR-ROM cart */
    wr(0x5010, 0x20);
    TM_CHECK(!c.chr_is_ram && (c.chr_wmask == 0xFF), "176 bit5 maps writable CHR-RAM");
    cart_ppu_write(&c, 0x0005, 0x5A);
    TM_CHECK(cart_ppu_read(&c, 0x0005) == 0x5A, "176 CHR-RAM r/w");
    wr(0x5010, 0x00);
    TM_CHECK(c.chr_wmask == 0 && tm_chr_bank(&c, 0) == 0x10, "176 back to CHR-ROM (got %x)", tm_chr_bank(&c, 0));
    wr(0x5012, 0x00);
    /* extended mode (bit 1 of $5xx3) */
    wr(0x5013, 0x02);
    TM_CHECK(prg_is(5, 0x46, 0x7E, 0x7F), "176 ext power-on regs 8/9 ($FE/$FF wrap on 1 MiB) (got %x %x %x %x)", tm_prg_bank(&c, 4), tm_prg_bank(&c, 5), tm_prg_bank(&c, 6), tm_prg_bank(&c, 7));
    mmc3r(8, 0x21); mmc3r(9, 0x22);
    TM_CHECK(prg_is(5, 0x46, 0x21, 0x22), "176 ext regs 8/9");
    wr(0x8000, 0x40);
    TM_CHECK(prg_is(0x21, 0x46, 5, 0x22), "176 ext PRG inversion swaps 6/8");
    wr(0x8000, 0x00);
    mmc3r(0, 0x10); mmc3r(1, 0x20); mmc3r(10, 0x31); mmc3r(11, 0x41);
    TM_CHECK(tm_chr_bank(&c, 0) == 0x10 && tm_chr_bank(&c, 1) == 0x31 && tm_chr_bank(&c, 2) == 0x20 && tm_chr_bank(&c, 3) == 0x41, "176 ext CHR 1K regs");
    wr(0x8000, 0x80);
    TM_CHECK(tm_chr_bank(&c, 4) == 0x10 && tm_chr_bank(&c, 5) == 0x31 && tm_chr_bank(&c, 0) == 0xB3, "176 ext CHR inversion");
    wr(0x8000, 0x00);
    wr(0x5013, 0x44);   /* "disable" value used by multicarts */
    TM_CHECK(prg_is(5, 6, 0x3E, 0x3F) && tm_chr_bank(&c, 1) == 0x11, "176 ext off");
    /* $E003 mask: $8003 is not $8001 */
    wr(0x8000, 6); wr(0x8003, 0x09);
    TM_CHECK(tm_prg_bank(&c, 4) == 5, "176 $E003 mask");
    /* mirroring + WRAM */
    wr(0xA000, 0);
    TM_CHECK(tm_nt(&c, 1) == 1 && tm_nt(&c, 2) == 0, "176 V");
    wr(0xA000, 1);
    TM_CHECK(tm_nt(&c, 1) == 0 && tm_nt(&c, 2) == 1, "176 H");
    wr(0xA000, 3);
    TM_CHECK(tm_nt(&c, 1) == 0 && tm_nt(&c, 2) == 1, "176 sub 0 has no single screen");
    wr(0xA001, 0x00);
    TM_CHECK(c.prg_map[3] == NULL, "176 WRAM disable");
    wr(0xA001, 0x80); wr(0x6000, 0x77);
    TM_CHECK(cart_cpu_read(&c, 0x6000) == 0x77, "176 WRAM r/w");
    wr(0xA001, 0xC0); wr(0x6000, 0x11);
    TM_CHECK(cart_cpu_read(&c, 0x6000) == 0x77, "176 WRAM write protect");
    /* IRQ */
    irq_check(checks, fails, "176");

    /* submapper 1: 8-bit MMC3 PRG in mode 0, CNROM latch */
    TM_CHECK(tm_load(&c, &mapper_176, 1, 2048, 256, 0, 8, 1), "176/1 load");
    TM_CHECK(c.s.mmc3.variant == 0, "176/1 not MMC6");
    mmc3r(6, 0x85);
    TM_CHECK(prg_is(0x85, 1, 0xFE, 0xFF), "176/1 8-bit inner PRG");
    wr(0x5012, 0x04); wr(0x5010, 0x40);                 /* CNROM 32K */
    TM_CHECK(tm_chr_bank(&c, 0) == 32, "176/1 CNROM latch 0");
    wr(0x8000, 0x03);
    TM_CHECK(tm_chr_bank(&c, 0) == 56 && tm_chr_bank(&c, 7) == 63, "176/1 CNROM latch 3 (got %u)", tm_chr_bank(&c, 0));
    TM_CHECK(c.s.mmc3.bank_select == 6, "176/1 CNROM write kept from MMC3");
    wr(0x5010, 0x50);                                    /* CNROM 16K */
    TM_CHECK(tm_chr_bank(&c, 0) == 40, "176/1 CNROM 16K (got %u)", tm_chr_bank(&c, 0));
    wr(0x5010, 0x60);                                    /* NROM: latch off */
    TM_CHECK(tm_chr_bank(&c, 0) == 32, "176/1 NROM CHR");

    /* submapper 2: Waixing FS005 RAM configuration register, single screen, outer bits */
    TM_CHECK(tm_load(&c, &mapper_176, 2, 1024, 0, 8, 32, 1), "176/2 load");
    wr(0xA001, 0xA2);                                     /* ram cfg, bank 2, regs disabled: $5000 = WRAM */
    TM_CHECK(c.prg_map[3] == c.wram + 2 * 8192, "176/2 WRAM bank 2");
    wr(0x5013, 0x02);                                     /* goes to WRAM, not to $5xx3 */
    TM_CHECK(c.s.mmc3.ext[3] == 0, "176/2 $5000 window is WRAM");
    TM_CHECK(cart_cpu_read(&c, 0x5013) == 0x02 && c.wram[0x5013] == 0x02, "176/2 $5000 window reads WRAM bank 2 upper 4K");
    TM_CHECK(cart_cpu_read(&c, 0x7013) == 0x02, "176/2 window aliases $7000 of bank 2");
    wr(0xA000, 2);
    TM_CHECK(tm_nt(&c, 0) == 0 && tm_nt(&c, 3) == 0, "176/2 1scA");
    wr(0xA000, 3);
    TM_CHECK(tm_nt(&c, 0) == 1 && tm_nt(&c, 3) == 1, "176/2 1scB");
    wr(0xA001, 0xE0);                                     /* regs enabled */
    wr(0x5010, 0x08);
    mmc3r(6, 0);
    TM_CHECK(tm_prg_bank(&c, 4) == 0, "176/2 A21 wraps on 1 MiB");
    TM_CHECK(c.prg_map[3] == c.wram, "176/2 WRAM bank 0");
    TM_CHECK(cart_cpu_read(&c, 0x5013) == c.open_bus, "176/2 $5000 not WRAM when regs on");
    wr(0xA001, 0x80);
    wr(0xA000, 2);
    TM_CHECK(tm_nt(&c, 1) == 1 && tm_nt(&c, 2) == 0, "176/2 no single screen without ram cfg (V)");

    /* submapper 2 with CHR-ROM: $A001.2 makes CHR banks 0-7 RAM */
    TM_CHECK(tm_load(&c, &mapper_176, 2, 512, 256, 0, 32, 1), "176/2 chr load");
    mmc3r(2, 0x03); mmc3r(3, 0x20);
    wr(0xA001, 0xE4);
    TM_CHECK((c.chr_wmask & 0x10) && !(c.chr_wmask & 0x20), "176/2 bank<8 is CHR-RAM, bank>=8 ROM");
    TM_CHECK(tm_chr_bank(&c, 5) == 0x20, "176/2 ROM bank kept");

    /* submapper 3: MSB registers at $5xx5/$5xx6 */
    TM_CHECK(tm_load(&c, &mapper_176, 3, 2048, 1024, 0, 0, 1), "176/3 load");
    TM_CHECK(c.s.mmc3.variant == 0, "176/3 not MC-ACC");
    wr(0x5015, 0x01);     /* PRG A21 -> beyond 2 MiB: wraps; check on 8K value via state */
    TM_CHECK(c.s.mmc3.ext[4] == 1, "176/3 $5xx5 stored");
    wr(0x5014, 0x55);
    TM_CHECK(c.s.mmc3.ext[0] == 0, "176/3 $5xx4 is not a mode mirror");
    wr(0x5015, 0x00); wr(0x5011, 0x40);
    TM_CHECK(tm_prg_bank(&c, 4) == 0x00, "176/3 mode 0: all 8 bits from MMC3 (got %x)", tm_prg_bank(&c, 4));
    wr(0x5010, 0x01);
    TM_CHECK(tm_prg_bank(&c, 4) == 0x80 && tm_prg_bank(&c, 7) == 0x9F, "176/3 mode 1 base (got %x)", tm_prg_bank(&c, 4));
    wr(0x5016, 0x01); wr(0x5012, 0x00); wr(0x5010, 0x40);
    TM_CHECK(tm_chr_bank(&c, 0) == 0, "176/3 CHR A21 wraps on 1 MiB");
    TM_CHECK(c.s.mmc3.ext[5] == 1, "176/3 $5xx6 stored");

    /* submapper 5: PRG MSB at $4800 */
    TM_CHECK(tm_load(&c, &mapper_176, 5, 2048, 256, 0, 0, 1), "176/5 load");
    wr(0x4800, 0x01); wr(0x5011, 0x03);   /* base = 0x03 | 0x20 (16K) -> 8K or = 0x40 */
    TM_CHECK(tm_prg_bank(&c, 4) == 0x40 && tm_prg_bank(&c, 7) == 0x7F, "176/5 $4800 (got %x)", tm_prg_bank(&c, 4));

    /* submapper 4: PRG A21 from $5xx2 bit 7 */
    TM_CHECK(tm_load(&c, &mapper_176, 4, 4096, 256, 0, 0, 1), "176/4 load");
    wr(0x5012, 0x80);
    TM_CHECK(tm_prg_bank(&c, 4) == 0x100, "176/4 A21 (got %x)", tm_prg_bank(&c, 4));
    irq_check(checks, fails, "176/4");
}

/* ------------------------------------------------------------------------------------------------ */
static void t_37_47(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_037, 0, 256, 256, 0, 0, 1), "37 load");
    TM_CHECK(prg_is(0, 1, 6, 7) && tm_chr_bank(&c, 0) == 0, "37 power-on (SMB block)");
    TM_CHECK(c.prg_map[3] == NULL, "37 no PRG-RAM");
    mmc3r(6, 0x0B);
    TM_CHECK(tm_prg_bank(&c, 4) == 3, "37 block 0 is 64K");
    wr(0x6000, 3);
    TM_CHECK(prg_is(0x0B, 9, 0x0E, 0x0F), "37 BB=3: A16 forced (got %u)", tm_prg_bank(&c, 4));
    wr(0x6000, 4);
    TM_CHECK(prg_is(0x1B, 0x11, 0x1E, 0x1F), "37 Q=1: 128K");
    mmc3r(0, 0x84);
    TM_CHECK(tm_chr_bank(&c, 0) == 0x84, "37 Q=1: CHR A17");
    wr(0x6000, 7);
    TM_CHECK(prg_is(0x1B, 0x19, 0x1E, 0x1F) && tm_chr_bank(&c, 0) == 0x84, "37 value 7");
    wr(0x6000, 0);
    TM_CHECK(tm_chr_bank(&c, 0) == 0x04 && tm_prg_bank(&c, 4) == 3, "37 value 0");
    wr(0xA001, 0xC0); wr(0x6000, 4);
    TM_CHECK(tm_prg_bank(&c, 4) == 3, "37 latch blocked while PRG-RAM write-protected");
    wr(0xA001, 0x00); wr(0x6000, 4);
    TM_CHECK(tm_prg_bank(&c, 4) == 3, "37 latch blocked while PRG-RAM disabled");
    wr(0xA001, 0x80);
    TM_CHECK(c.prg_map[3] == NULL, "37 still no PRG-RAM after $A001");
    wr(0x7FFF, 4);
    TM_CHECK(tm_prg_bank(&c, 4) == 0x1B, "37 latch at $7FFF");
    wr(0xA000, 1);
    TM_CHECK(tm_nt(&c, 1) == 0 && tm_nt(&c, 2) == 1, "37 MMC3 mirroring");
    irq_check(checks, fails, "37");

    TM_CHECK(tm_load(&c, &mapper_047, 0, 256, 256, 0, 0, 1), "47 load");
    TM_CHECK(prg_is(0, 1, 14, 15), "47 power-on block 0");
    mmc3r(6, 0x13); mmc3r(2, 0x85);
    TM_CHECK(tm_prg_bank(&c, 4) == 3 && tm_chr_bank(&c, 4) == 5, "47 128K windows");
    wr(0x6000, 1);
    TM_CHECK(prg_is(0x13, 0x11, 0x1E, 0x1F) && tm_chr_bank(&c, 4) == 0x85, "47 block 1");
    wr(0xA001, 0xC0); wr(0x6000, 0);
    TM_CHECK(tm_prg_bank(&c, 4) == 0x13, "47 write-protected");
    wr(0xA001, 0x80); wr(0x6000, 0xFE);
    TM_CHECK(tm_prg_bank(&c, 4) == 3, "47 only bit 0");
    irq_check(checks, fails, "47");
}

/* ------------------------------------------------------------------------------------------------ */
static void t_189(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_189, 0, 128, 256, 0, 0, 1), "189 load");
    TM_CHECK(prg_is(0, 1, 2, 3), "189 power-on 32K bank 0");
    mmc3r(6, 9); mmc3r(7, 9);
    TM_CHECK(prg_is(0, 1, 2, 3), "189 MMC3 PRG regs ignored");
    wr(0x4120, 0x10);
    TM_CHECK(prg_is(4, 5, 6, 7), "189 $4120 high nibble");
    wr(0x6000, 0x02);
    TM_CHECK(prg_is(8, 9, 10, 11), "189 $6000 low nibble");
    wr(0x8000, 0x40);
    TM_CHECK(prg_is(8, 9, 10, 11), "189 PRG mode ignored");
    wr(0xA001, 0x80);
    TM_CHECK(c.prg_map[3] == NULL, "189 no PRG-RAM");
    mmc3r(0, 0x22); mmc3r(5, 0x77);
    TM_CHECK(tm_chr_bank(&c, 0) == 0x22 && tm_chr_bank(&c, 1) == 0x23 && tm_chr_bank(&c, 7) == 0x77, "189 MMC3 CHR");
    wr(0xA000, 0);
    TM_CHECK(tm_nt(&c, 1) == 1, "189 mirroring");
    irq_check(checks, fails, "189");
}

/* ------------------------------------------------------------------------------------------------ */
static void t_361_366(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_361, 0, 512, 512, 0, 8, 1), "361 load");
    TM_CHECK(prg_is(0, 1, 14, 15), "361 power-on outer 0");
    wr(0xA001, 0x00);                         /* WRAM off: register still works */
    wr(0x7000, 0x20);
    TM_CHECK(prg_is(0x20, 0x21, 0x2E, 0x2F) && tm_chr_bank(&c, 0) == 0x100, "361 outer 2");
    mmc3r(6, 0x35); mmc3r(0, 0x96);
    TM_CHECK(tm_prg_bank(&c, 4) == 0x25 && tm_chr_bank(&c, 0) == 0x116, "361 inner masked");
    wr(0xA001, 0x80); wr(0x7123, 0x30);
    TM_CHECK(tm_prg_bank(&c, 4) == 0x35 && cart_cpu_read(&c, 0x7123) == 0x30, "361 write also lands in WRAM");
    wr(0x6000, 0x00);
    TM_CHECK(tm_prg_bank(&c, 4) == 0x35, "361 $6000 is plain WRAM");
    irq_check(checks, fails, "361");

    TM_CHECK(tm_load(&c, &mapper_366, 0, 1024, 1024, 0, 8, 1), "366 load");
    TM_CHECK(prg_is(0, 1, 14, 15), "366 power-on outer 0");
    wr(0x6830, 0xFF);                          /* address bits select, data ignored */
    TM_CHECK(prg_is(0x30, 0x31, 0x3E, 0x3F) && tm_chr_bank(&c, 0) == 0x180, "366 outer 3");
    wr(0x6850, 0x00);
    TM_CHECK(tm_prg_bank(&c, 4) == 0x50, "366 outer 5");
    wr(0x68F0, 0x00);                          /* lock, outer 7 */
    TM_CHECK(tm_prg_bank(&c, 4) == 0x70, "366 outer 7 + lock");
    wr(0x6810, 0x00);
    TM_CHECK(tm_prg_bank(&c, 4) == 0x70, "366 locked");
    TM_CHECK(cart_cpu_read(&c, 0x6810) == 0x00 && cart_cpu_read(&c, 0x6830) == 0xFF, "366 writes land in WRAM");
    wr(0x7830, 0);
    irq_check(checks, fails, "366");
}

/* ------------------------------------------------------------------------------------------------ */
static void t_238(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_238, 0, 128, 256, 0, 0, 1), "238 load");
    TM_CHECK(prg_is(0, 1, 14, 15), "238 power-on MMC3");
    TM_CHECK(cart_cpu_read(&c, 0x4020) == 0, "238 power-on protection 0");
    static const uint8_t want[4] = { 0, 2, 2, 3 };
    for (unsigned v = 0; v < 4; v++) {
        wr(0x6000, (uint8_t)(0xF0 | v));
        TM_CHECK(cart_cpu_read(&c, 0x5000) == want[v] && cart_cpu_read(&c, 0x7FFF) == want[v], "238 LUT %u", v);
    }
    wr(0x4020, 1);
    TM_CHECK(cart_cpu_read(&c, 0x6000) == 2, "238 $4020 write");
    wr(0xA001, 0x80);
    TM_CHECK(c.prg_map[3] == NULL, "238 no PRG-RAM");
    mmc3r(6, 5); mmc3r(1, 9);
    TM_CHECK(tm_prg_bank(&c, 4) == 5 && tm_chr_bank(&c, 2) == 8 && tm_chr_bank(&c, 3) == 9, "238 MMC3 banks");
    irq_check(checks, fails, "238");
}

/* ------------------------------------------------------------------------------------------------ */
static void t_262(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_262, 0, 256, 512, 0, 0, 2), "262 load");
    TM_CHECK(prg_is(0, 1, 30, 31) && tm_chr_bank(&c, 0) == 0 && tm_chr_bank(&c, 4) == 4, "262 power-on");
    TM_CHECK(tm_nt(&c, 2) == -1, "262 four-screen");
    mmc3r(0, 0x10); mmc3r(1, 0x20); mmc3r(2, 0x30); mmc3r(3, 0x31); mmc3r(4, 0x40); mmc3r(5, 0x41);
    wr(0x4100, 0x08);
    TM_CHECK(tm_chr_bank(&c, 0) == 0x110 && tm_chr_bank(&c, 1) == 0x111 && tm_chr_bank(&c, 2) == 0x20, "262 bit 3 -> $0000-$07FF");
    wr(0x4100, 0x04);
    TM_CHECK(tm_chr_bank(&c, 0) == 0x10 && tm_chr_bank(&c, 3) == 0x121, "262 bit 2 -> $0800-$0FFF");
    wr(0x4100, 0x01);
    TM_CHECK(tm_chr_bank(&c, 4) == 0x130 && tm_chr_bank(&c, 5) == 0x131 && tm_chr_bank(&c, 6) == 0x40, "262 bit 0 -> $1000-$17FF");
    wr(0x4100, 0x02);
    TM_CHECK(tm_chr_bank(&c, 6) == 0x140 && tm_chr_bank(&c, 7) == 0x141 && tm_chr_bank(&c, 4) == 0x30, "262 bit 1 -> $1800-$1FFF");
    wr(0x8000, 0x80);   /* CHR inversion: bit 1 still follows PPU $1800 (now R1) */
    TM_CHECK(tm_chr_bank(&c, 6) == 0x120 && tm_chr_bank(&c, 0) == 0x30, "262 per-PPU-address after inversion");
    wr(0x8000, 0x00);
    wr(0x4100, 0x40);
    TM_CHECK(c.chr_wmask == 0xFF, "262 CHR-RAM");
    cart_ppu_write(&c, 0x1C02, 0xA5);
    TM_CHECK(cart_ppu_read(&c, 0x1C02) == 0xA5, "262 CHR-RAM r/w");
    wr(0x4100, 0x00);
    TM_CHECK(c.chr_wmask == 0 && tm_chr_bank(&c, 0) == 0x10, "262 back to CHR-ROM");
    c.open_bus = 0xFF;
    TM_CHECK((cart_cpu_read(&c, 0x4100) & 0x80) == 0, "262 jumper reads 0 (Street Heroes)");
    mmc3r(6, 7);
    TM_CHECK(tm_prg_bank(&c, 4) == 7, "262 MMC3 PRG");
    irq_check(checks, fails, "262");
}

void tm_mmc3x(int *checks, int *fails) {
    t_176(checks, fails);
    t_37_47(checks, fails);
    t_189(checks, fails);
    t_361_366(checks, fails);
    t_238(checks, fails);
    t_262(checks, fails);
}
