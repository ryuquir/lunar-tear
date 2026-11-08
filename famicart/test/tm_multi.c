/* Tests for src/core/mappers/m_port_multi.c (27, 41, 59, 217, 228, 232, 234, 521). */
#include "tm_util.h"

extern const mapper_desc_t mapper_027, mapper_041, mapper_059, mapper_217, mapper_228, mapper_232, mapper_234, mapper_521;
void m234_rom_read(cart_t *c, uint16_t a);
static cart_t c;

static void wr(uint16_t a, uint8_t v) { cart_cpu_write(&c, a, v); }
static bool is_v(void) { return tm_nt(&c, 0) == 0 && tm_nt(&c, 1) == 1 && tm_nt(&c, 2) == 0 && tm_nt(&c, 3) == 1; }
static bool is_h(void) { return tm_nt(&c, 0) == 0 && tm_nt(&c, 1) == 0 && tm_nt(&c, 2) == 1 && tm_nt(&c, 3) == 1; }
static bool is_1(int p) { for (unsigned i = 0; i < 4; i++) if (tm_nt(&c, i) != p) return false; return true; }
static bool prg32(uint32_t b) { for (unsigned i = 0; i < 4; i++) if (tm_prg_bank(&c, 4 + i) != b * 4 + i) return false; return true; }
static bool chr8(uint32_t b) { for (unsigned i = 0; i < 8; i++) if (tm_chr_bank(&c, i) != b * 8 + i) return false; return true; }
static bool prg16(unsigned slot, uint32_t b) { return tm_prg_bank(&c, 4 + slot * 2) == b * 2 && tm_prg_bank(&c, 5 + slot * 2) == b * 2 + 1; }

static void t_059(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_059, 0, 128, 64, 0, 0, 0), "59 load");
    TM_CHECK(prg32(0) && chr8(0) && is_v(), "59 power-on");
    wr(0x8000 | 0x0035, 0);                 /* S=0, PP=1 (p=1 ignored), M=0, CHR 5 */
    TM_CHECK(prg32(1) && chr8(5) && is_v(), "59 NROM-256 bank 1, chr 5");
    wr(0x8000 | 0x00EA, 0);                 /* S=1, PPp=6, M=1, CHR 2 */
    TM_CHECK(prg16(0, 6) && prg16(1, 6) && chr8(2) && is_h(), "59 NROM-128 bank 6, H");
    wr(0x8000 | 0x0110, 0);                 /* jumper read */
    TM_CHECK(cart_cpu_read(&c, 0x8000) == 0 && cart_cpu_read(&c, 0xFFFC) == 0 && cart_cpu_read(&c, 0xC123) == 0, "59 jumper reads 0");
    wr(0x8000 | 0x0010, 0);
    TM_CHECK(prg32(0) && cart_cpu_read(&c, 0xA000) == 1, "59 ROM back after D=0");
    wr(0x8000 | 0x0227, 0);                 /* lock with chr 7 */
    TM_CHECK(chr8(7), "59 lock write applies");
    wr(0x8000 | 0x0030, 0);
    TM_CHECK(chr8(7) && prg32(1), "59 locked");
    mapper_attach_desc(&c, &mapper_059, 0);
    wr(0x8003, 0);
    TM_CHECK(chr8(3), "59 reset unlocks");
}

static void t_041(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_041, 0, 256, 128, 0, 0, 0), "41 load");
    TM_CHECK(prg32(0) && chr8(0) && is_v() && c.prg_map[3] == NULL, "41 power-on");
    wr(0x8000, 3);                          /* inner disabled while bank < 4 */
    TM_CHECK(chr8(0), "41 inner gated");
    wr(0x6000 | 0x3D, 0);                   /* M=1 CC=3 EPP=5 */
    TM_CHECK(prg32(5) && chr8(12) && is_h(), "41 outer (prg %u chr %u)", tm_prg_bank(&c, 4), tm_chr_bank(&c, 0));
    wr(0x8000, 2);
    TM_CHECK(chr8(14), "41 inner CHR");
    c.bus_conflicts = true;
    wr(0xA000, 3);                          /* ROM byte at $A000 = bank 21 = 0x15: 3 & 0x15 = 1 */
    TM_CHECK(chr8(13), "41 bus conflict (chr %u)", tm_chr_bank(&c, 0));
    c.bus_conflicts = false;
    wr(0x6800, 0);                          /* outside $6000-$67FF */
    TM_CHECK(prg32(5), "41 $6800 ignored");
    wr(0x600A, 0);                          /* E=0, PP=2, CC=1 */
    TM_CHECK(prg32(2) && chr8(5) && is_v(), "41 outer keeps inner (chr %u)", tm_chr_bank(&c, 0));
    wr(0x8000, 0);
    TM_CHECK(chr8(5), "41 inner gated again");
}

static void t_228(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_228, 0, 1536, 512, 0, 0, 0), "228 load");
    TM_CHECK(prg32(0) && chr8(0) && is_v(), "228 power-on");
    /* chip 1, bank 5, S=1, CHR hi 3, lo 2, H */
    wr((uint16_t)(0x8000 | 0x2000 | (1 << 11) | (5 << 6) | 0x20 | 3), 2);
    TM_CHECK(prg16(0, 37) && prg16(1, 37) && chr8(14) && is_h(), "228 16K mode (prg %u)", tm_prg_bank(&c, 4));
    wr((uint16_t)(0x8000 | (3 << 11) | (7 << 6)), 1);   /* chip 3 -> file chip 2, 32K mode */
    TM_CHECK(prg16(0, 70) && prg16(1, 71) && chr8(1) && is_v(), "228 chip 3 32K (prg %u)", tm_prg_bank(&c, 4));
    wr((uint16_t)(0x8000 | (2 << 11)), 0);              /* chip 2: open bus */
    TM_CHECK(c.prg_map[4] == NULL && c.prg_map[7] == NULL, "228 chip 2 unmapped");
    c.open_bus = 0x5A;
    TM_CHECK(cart_cpu_read(&c, 0x9000) == 0x5A, "228 chip 2 open bus");
    wr(0x8000, 0);
    TM_CHECK(prg32(0), "228 back to chip 0");
    wr(0x4020, 0xA5); wr(0x4023, 0x0C); wr(0x5FFD, 0x07);  /* $5FFD mirrors $4021 */
    c.open_bus = 0xF0;
    TM_CHECK(cart_cpu_read(&c, 0x4020) == 0xF5, "228 nibble RAM 0");
    c.open_bus = 0x30;
    TM_CHECK(cart_cpu_read(&c, 0x4021) == 0x37 && cart_cpu_read(&c, 0x4027) == 0x3C, "228 nibble RAM mirrors");
    /* Cheetahmen II size (256K): chip bits just wrap */
    TM_CHECK(tm_load(&c, &mapper_228, 0, 256, 128, 0, 0, 0), "228 load small");
    wr((uint16_t)(0x8000 | (9 << 6) | 0x20), 0);
    TM_CHECK(prg16(0, 9) && prg16(1, 9), "228 small 16K");
}

static void t_217(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_217, 0, 1024, 1024, 0, 0, 1), "217 load");
    /* reset: E1=$FF -> PRG or $60 (8K), mask $1F; CHR or $300 */
    TM_CHECK(tm_prg_bank(&c, 4) == 0x60 && tm_prg_bank(&c, 5) == 0x61 && tm_prg_bank(&c, 6) == 0x7E && tm_prg_bank(&c, 7) == 0x7F, "217 power-on prg (%x)", tm_prg_bank(&c, 4));
    TM_CHECK(tm_chr_bank(&c, 0) == 0x300 && tm_chr_bank(&c, 4) == 0x304, "217 power-on chr (%x)", tm_chr_bank(&c, 0));
    /* scrambled (E2=3): $8001 = select (perm), $A000 = data */
    wr(0x8001, 1);      /* lut[1] = 6 -> R6 */
    wr(0xA000, 5);
    TM_CHECK(tm_prg_bank(&c, 4) == 0x65, "217 scrambled R6 (%x)", tm_prg_bank(&c, 4));
    wr(0xA000, 9);      /* second data write without a new select is ignored */
    TM_CHECK(tm_prg_bank(&c, 4) == 0x65, "217 one data write per select");
    wr(0x8001, 0);      /* lut[0] = 0 -> R0 (2K CHR) */
    wr(0xA000, 0x20);
    TM_CHECK(tm_chr_bank(&c, 0) == 0x320 && tm_chr_bank(&c, 1) == 0x321, "217 scrambled R0");
    wr(0xA001, 1);      /* scrambled mirroring */
    TM_CHECK(is_h(), "217 scrambled mirroring H");
    wr(0xA001, 0);
    TM_CHECK(is_v(), "217 scrambled mirroring V");
    /* unscrambled */
    wr(0x5007, 0);
    wr(0x8000, 7); wr(0x8001, 3);
    TM_CHECK(tm_prg_bank(&c, 5) == 0x63, "217 plain R7");
    wr(0xA000, 1);
    TM_CHECK(is_h(), "217 plain mirroring");
    /* E1: narrow masks, outer 1 */
    wr(0x5001, 0x11);   /* D3=0: PRG (b & $0F) | $10 | $20; CHR (b & $7F) | ($11<<3 & $80 = $80) | $100 */
    TM_CHECK(tm_prg_bank(&c, 4) == 0x35 && tm_prg_bank(&c, 5) == 0x33 && tm_prg_bank(&c, 7) == 0x3F, "217 narrow prg (%x)", tm_prg_bank(&c, 4));
    TM_CHECK(tm_chr_bank(&c, 0) == 0x1A0, "217 narrow chr (%x)", tm_chr_bank(&c, 0));
    /* NROM 16K mode */
    wr(0x5001, 0x0A); wr(0x5000, 0x83);   /* wide: bank16 = 3 | (0x0A<<4 & 0x30 = 0x20) = 0x23 -> 8K 0x46 -> &1F | 0x40 */
    TM_CHECK(tm_prg_bank(&c, 4) == 0x46 && tm_prg_bank(&c, 5) == 0x47 && tm_prg_bank(&c, 6) == 0x46 && tm_prg_bank(&c, 7) == 0x47, "217 16K mode (%x)", tm_prg_bank(&c, 4));
    wr(0x8000, 6); wr(0x8001, 9);         /* MMC3 PRG write keeps the 16K mode */
    TM_CHECK(tm_prg_bank(&c, 4) == 0x46, "217 16K mode sticks");
    wr(0x5000, 0x00);
    TM_CHECK(tm_prg_bank(&c, 4) == 0x49 && tm_prg_bank(&c, 7) == 0x5F, "217 MMC3 mode back (%x)", tm_prg_bank(&c, 4));
    /* IRQ: MMC3 A12 counter */
    wr(0xC000, 1); wr(0xC001, 0); wr(0xE001, 0);
    for (int line = 0; line < 3; line++) { for (int k = 0; k < 8; k++) cart_ppu_read(&c, 0x0000); cart_ppu_read(&c, 0x1000); }
    TM_CHECK(c.irq_line == 1, "217 IRQ fires");
    wr(0xE000, 0);
    TM_CHECK(c.irq_line == 0, "217 IRQ ack");
}

static void t_232(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_232, 0, 256, 0, 8, 0, 1), "232 load");
    TM_CHECK(prg16(0, 0) && prg16(1, 3) && is_v(), "232 power-on");
    wr(0x8000, 0x10);   /* block 2 */
    TM_CHECK(prg16(0, 8) && prg16(1, 11), "232 block 2");
    wr(0xC000, 2);
    TM_CHECK(prg16(0, 10) && prg16(1, 11), "232 page 2");
    wr(0xA000, 0x08);   /* block 1 */
    TM_CHECK(prg16(0, 6) && prg16(1, 7), "232 block 1");
    TM_CHECK(c.chr_wmask == 0xFF, "232 CHR-RAM");
    TM_CHECK(tm_load(&c, &mapper_232, 1, 256, 0, 8, 0, 0), "232/1 load");
    wr(0x8000, 0x10);   /* Aladdin: D4 -> block bit 0 */
    TM_CHECK(prg16(0, 4) && prg16(1, 7), "232/1 swapped D4");
    wr(0x8000, 0x08);   /* D3 -> block bit 1 */
    TM_CHECK(prg16(0, 8) && prg16(1, 11), "232/1 swapped D3");
    TM_CHECK(is_h(), "232 hard-wired mirroring");
}

static void t_234(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_234, 0, 512, 512, 0, 0, 0), "234 load");
    TM_CHECK(prg32(0) && chr8(0) && is_v(), "234 power-on");
    /* write path (with bus conflicts off): outer CNROM block 3, mirroring H */
    wr(0xFF80, 0x83);
    TM_CHECK(prg32(3) && chr8(12) && is_h(), "234 CNROM outer (prg %u chr %u)", tm_prg_bank(&c, 4), tm_chr_bank(&c, 0));
    wr(0xFFE8, 0x20);   /* CC = 2 */
    TM_CHECK(chr8(14) && prg32(3), "234 CNROM inner CHR");
    wr(0xFF80, 0x01);
    TM_CHECK(prg32(3), "234 outer locked");
    wr(0xFFC0, 0xFF);
    TM_CHECK(prg32(3) && chr8(14), "234 lockout reg ignored");
    /* read path: reads latch the ROM byte. Fresh cart, NINA-03 mode via a read of a ROM byte $46 */
    TM_CHECK(tm_load(&c, &mapper_234, 0, 512, 512, 0, 0, 0), "234 reload");
    /* bank 0 at $8000; the byte at $FF80 is in 8K page 3 -> value 3 (offset 1 holds 0) */
    TM_CHECK(c.mapper->peek(&c, 0xFF80, 0) == 3 && prg32(0), "234 peek no side effect");
    uint8_t v = c.mapper->read(&c, 0xFF80, 0);
    TM_CHECK(v == 3 && prg32(3) && chr8(12), "234 read latches ROM byte (prg %u)", tm_prg_bank(&c, 4));
    /* now in bank 3: $FFE8 holds page 15 = 0x0F -> inner = 0x0F & 0x71 = 0x01 (CNROM: no effect on PRG) */
    m234_rom_read(&c, 0xFFE8);
    TM_CHECK(prg32(3) && c.s.g.regs[1] == 0x01, "234 m234_rom_read inner");
    m234_rom_read(&c, 0xFF00);   /* not a register */
    TM_CHECK(prg32(3), "234 non-register read ignored");
    /* NINA-03: outer with O=1, BBB=2 (0x44), inner P=1 c=5 */
    TM_CHECK(tm_load(&c, &mapper_234, 0, 512, 512, 0, 0, 0), "234 reload 2");
    wr(0xFF80, 0x44);
    TM_CHECK(prg32(4) && chr8(16), "234 NINA outer (prg %u chr %u)", tm_prg_bank(&c, 4), tm_chr_bank(&c, 0));
    wr(0xFFF7, 0x51);
    TM_CHECK(prg32(5) && chr8(21), "234 NINA inner (prg %u chr %u)", tm_prg_bank(&c, 4), tm_chr_bank(&c, 0));
    c.bus_conflicts = true;
    wr(0xFFE9, 0x71);   /* ROM byte in bank 5, page 23 = 0x17 -> 0x11 */
    TM_CHECK(c.s.g.regs[1] == 0x11 && chr8(17), "234 bus conflict inner (%02x)", c.s.g.regs[1]);
}

static void t_027(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_027, 0, 256, 512, 0, 8, 0), "27 load");
    TM_CHECK(tm_prg_bank(&c, 4) == 0 && tm_prg_bank(&c, 5) == 1 && tm_prg_bank(&c, 6) == 30 && tm_prg_bank(&c, 7) == 31, "27 power-on prg");
    TM_CHECK(tm_chr_bank(&c, 0) == 0 && tm_chr_bank(&c, 7) == 7 && c.prg_map[3] != NULL, "27 power-on chr / WRAM");
    wr(0x8000, 5); wr(0xA000, 9);
    TM_CHECK(tm_prg_bank(&c, 4) == 5 && tm_prg_bank(&c, 5) == 9 && tm_prg_bank(&c, 6) == 30, "27 PRG regs");
    wr(0x9002, 2);
    TM_CHECK(tm_prg_bank(&c, 4) == 30 && tm_prg_bank(&c, 6) == 5, "27 PRG swap");
    wr(0x9002, 0);
    wr(0x9000, 1); TM_CHECK(is_h(), "27 H");
    wr(0x9001, 2); TM_CHECK(is_1(0), "27 1scA");
    wr(0x9000, 3); TM_CHECK(is_1(1), "27 1scB");
    wr(0x9000, 0); TM_CHECK(is_v(), "27 V");
    wr(0xB000, 0x0A); wr(0xB001, 0x1F);   /* bank 0 = $1FA = 506 (9 bits) */
    TM_CHECK(tm_chr_bank(&c, 0) == 506, "27 9-bit CHR (%u)", tm_chr_bank(&c, 0));
    wr(0xB002, 3); wr(0xB003, 1);
    TM_CHECK(tm_chr_bank(&c, 1) == 19, "27 CHR1");
    wr(0xE002, 4); wr(0xE003, 2);
    TM_CHECK(tm_chr_bank(&c, 7) == 36, "27 CHR7 (%u)", tm_chr_bank(&c, 7));
    wr(0xD000, 1); wr(0xD001, 0);
    TM_CHECK(tm_chr_bank(&c, 4) == 1, "27 CHR4");
    /* IRQ, cycle mode: latch $FD, enable -> fires after 3 M2 */
    wr(0xF000, 0x0D); wr(0xF001, 0x0F); wr(0xF002, 0x07);
    for (int i = 0; i < 2; i++) cart_cpu_cycle(&c);
    TM_CHECK(c.irq_line == 0, "27 IRQ not yet");
    cart_cpu_cycle(&c);
    TM_CHECK(c.irq_line == 1, "27 IRQ cycle mode");
    wr(0xF003, 0);
    TM_CHECK(c.irq_line == 0, "27 IRQ ack");
    /* ack copied R (=1) into E: keeps counting from the latch */
    for (int i = 0; i < 3; i++) cart_cpu_cycle(&c);
    TM_CHECK(c.irq_line == 1, "27 IRQ retrigger");
    /* scanline mode: latch $FF -> one scanline (113.67 M2) */
    wr(0xF000, 0x0F); wr(0xF002, 0x02);
    for (int i = 0; i < 113; i++) cart_cpu_cycle(&c);
    TM_CHECK(c.irq_line == 0, "27 scanline IRQ not yet");
    cart_cpu_cycle(&c);
    TM_CHECK(c.irq_line == 1, "27 scanline IRQ");
    wr(0xF002, 0);
    TM_CHECK(c.irq_line == 0, "27 IRQ disabled");
    /* CC-21 (32K PRG, 8K CHR) */
    TM_CHECK(tm_load(&c, &mapper_027, 0, 32, 8, 0, 0, 0), "27 CC-21 load");
    TM_CHECK(prg32(0) && tm_chr_bank(&c, 0) == 0 && tm_chr_bank(&c, 4) == 0, "27 CC-21 power-on");
    wr(0x8000, 1);
    TM_CHECK(tm_chr_bank(&c, 0) == 4 && tm_chr_bank(&c, 4) == 4 && is_1(1), "27 CC-21 data latch");
    wr(0x8002, 1);    /* address A0 = 0 */
    TM_CHECK(tm_chr_bank(&c, 0) == 0 && is_1(0), "27 CC-21 address latch");
    wr(0xFFFF, 0);
    TM_CHECK(tm_chr_bank(&c, 4) == 4 && is_1(1), "27 CC-21 address latch A0=1");
    TM_CHECK(tm_load(&c, &mapper_027, 0, 32, 16, 0, 0, 0), "27 CC-21 16K load");
    wr(0x8001, 0);
    TM_CHECK(chr8(1), "27 CC-21 16K CHR 8K bank");
}

static void t_521(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_521, 0, 272, 0, 8, 0, 1), "521 load");
    TM_CHECK(prg16(0, 0) && prg16(1, 16) && is_v(), "521 power-on (fixed %u)", tm_prg_bank(&c, 6));
    wr(0x5020, 0x0B);
    TM_CHECK(prg16(0, 11) && prg16(1, 16), "521 bank 11");
    wr(0x5030, 3);
    TM_CHECK(prg16(0, 11), "521 $5030 ignored");
    wr(0x5FEF, 4);    /* mask $F030: $5FEF & $F030 = $5020 */
    TM_CHECK(prg16(0, 4), "521 mirrored register");
    wr(0x8000, 2);
    TM_CHECK(prg16(0, 4), "521 $8000 not a register");
    TM_CHECK(c.chr_wmask == 0xFF, "521 CHR-RAM");
}

void tm_multi(int *checks, int *fails) {
    t_059(checks, fails); t_041(checks, fails); t_228(checks, fails); t_217(checks, fails);
    t_232(checks, fails); t_234(checks, fails); t_027(checks, fails); t_521(checks, fails);
}
