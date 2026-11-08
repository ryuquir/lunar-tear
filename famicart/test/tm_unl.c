/* Tests for src/core/mappers/m_port_unl.c (36, 38, 138, 139, 141, 144, 148, 168, 193) and mapper 158. */
#include "tm_util.h"

extern const mapper_desc_t mapper_036, mapper_038, mapper_138, mapper_139, mapper_141, mapper_144,
                           mapper_148, mapper_158, mapper_168, mapper_193, mapper_064;
static cart_t c;

static void wr(uint16_t a, uint8_t v) { cart_cpu_write(&c, a, v); }
static void s8259(uint8_t reg, uint8_t v) { wr(0x4100, reg); wr(0x4101, v); }

static void t_8259(int *checks, int *fails) {
    /* 141 (A, shift 1): 1K page = (r << 2) | (PPU A11..A10) */
    TM_CHECK(tm_load(&c, &mapper_141, 0, 128, 256, 0, 0, 0), "141 load");
    TM_CHECK(tm_prg_bank(&c, 4) == 0 && tm_prg_bank(&c, 7) == 3, "141 power-on prg");
    TM_CHECK(tm_chr_bank(&c, 0) == 0 && tm_chr_bank(&c, 1) == 1 && tm_chr_bank(&c, 2) == 2 && tm_chr_bank(&c, 3) == 3, "141 power-on chr");
    TM_CHECK(tm_nt(&c, 1) == 1 && tm_nt(&c, 2) == 0, "141 power-on V");
    TM_CHECK(c.prg_map[3] == NULL, "141 no PRG RAM");
    s8259(5, 3);
    TM_CHECK(tm_prg_bank(&c, 4) == 12 && tm_prg_bank(&c, 7) == 15, "141 prg 32K bank 3");
    s8259(0, 1); s8259(1, 2); s8259(2, 3); s8259(3, 4);
    TM_CHECK(tm_chr_bank(&c, 0) == 4 && tm_chr_bank(&c, 1) == 5, "141 R0 -> $0000 (got %u)", tm_chr_bank(&c, 0));
    TM_CHECK(tm_chr_bank(&c, 2) == 10 && tm_chr_bank(&c, 3) == 11, "141 R1 -> $0800 (A11 leaks: got %u)", tm_chr_bank(&c, 2));
    TM_CHECK(tm_chr_bank(&c, 4) == 12 && tm_chr_bank(&c, 5) == 13, "141 R2 -> $1000");
    TM_CHECK(tm_chr_bank(&c, 6) == 18 && tm_chr_bank(&c, 7) == 19, "141 R3 -> $1800");
    s8259(4, 1);
    TM_CHECK(tm_chr_bank(&c, 0) == 36 && tm_chr_bank(&c, 6) == 50, "141 R4 outer bank (got %u)", tm_chr_bank(&c, 0));
    s8259(7, 2);
    TM_CHECK(tm_nt(&c, 0) == 0 && tm_nt(&c, 1) == 0 && tm_nt(&c, 2) == 1 && tm_nt(&c, 3) == 1, "141 H");
    s8259(7, 4);
    TM_CHECK(tm_nt(&c, 0) == 0 && tm_nt(&c, 1) == 1 && tm_nt(&c, 2) == 1 && tm_nt(&c, 3) == 1, "141 (0,1,1,1)");
    s8259(7, 6);
    TM_CHECK(tm_nt(&c, 0) == 0 && tm_nt(&c, 1) == 0 && tm_nt(&c, 2) == 0 && tm_nt(&c, 3) == 0, "141 1scA");
    s8259(7, 3);   /* simple mode + H bits: mirroring forced V, all windows use R0 */
    TM_CHECK(tm_nt(&c, 1) == 1 && tm_nt(&c, 2) == 0, "141 simple forces V");
    TM_CHECK(tm_chr_bank(&c, 0) == 36 && tm_chr_bank(&c, 2) == 38 && tm_chr_bank(&c, 4) == 36 && tm_chr_bank(&c, 7) == 39, "141 simple uses R0");
    s8259(7, 0);
    wr(0x5100, 0); wr(0x5101, 7);  /* mask $C101 mirror */
    TM_CHECK(tm_chr_bank(&c, 0) == 60, "141 mirrored ports (got %u)", tm_chr_bank(&c, 0));
    wr(0x4100, 0x0D); wr(0x4101, 0xF9);  /* only D2-D0 matter: reg 5 <- 1 */
    TM_CHECK(tm_prg_bank(&c, 4) == 4, "141 D2-D0 only");
    wr(0x4102, 5);   /* A0 = 0: select, not data */
    wr(0x8100, 1);   /* A15 set: ignored */
    TM_CHECK(tm_prg_bank(&c, 4) == 4, "141 $4102/$8100 ignored");

    /* 138 (B, shift 0): 1K page = (r << 1) | A10 */
    TM_CHECK(tm_load(&c, &mapper_138, 0, 128, 128, 0, 0, 0), "138 load");
    s8259(0, 5); s8259(3, 2); s8259(4, 1);
    TM_CHECK(tm_chr_bank(&c, 0) == 26 && tm_chr_bank(&c, 1) == 27 && tm_chr_bank(&c, 6) == 20 && tm_chr_bank(&c, 7) == 21, "138 chr");
    /* 139 (C, shift 2): 1K page = (r << 3) | A12..A10 */
    TM_CHECK(tm_load(&c, &mapper_139, 0, 128, 512, 0, 0, 0), "139 load");
    s8259(0, 1); s8259(2, 3);
    TM_CHECK(tm_chr_bank(&c, 0) == 8 && tm_chr_bank(&c, 1) == 9 && tm_chr_bank(&c, 4) == 28 && tm_chr_bank(&c, 5) == 29, "139 chr");
}

static void t_148(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_148, 0, 64, 64, 0, 0, 1), "148 load");
    TM_CHECK(tm_prg_bank(&c, 4) == 0 && tm_chr_bank(&c, 0) == 0, "148 power-on");
    c.bus_conflicts = false;
    wr(0x8000, 0x0D);
    TM_CHECK(tm_prg_bank(&c, 4) == 4 && tm_prg_bank(&c, 7) == 7 && tm_chr_bank(&c, 0) == 40 && tm_chr_bank(&c, 7) == 47, "148 latch");
    TM_CHECK(tm_nt(&c, 1) == 1, "148 hard-wired V");
    /* bus conflict: ROM byte at $C000 (bank 6) is 6 -> 0x0F & 6 = 6 */
    c.bus_conflicts = true;
    wr(0xC000, 0x0F);
    TM_CHECK(tm_prg_bank(&c, 4) == 0 && tm_chr_bank(&c, 0) == 48, "148 bus conflict");
}

static void t_38(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_038, 0, 128, 32, 0, 0, 1), "38 load");
    TM_CHECK(tm_prg_bank(&c, 4) == 0 && tm_chr_bank(&c, 0) == 0, "38 power-on");
    wr(0x7000, 0x0B);
    TM_CHECK(tm_prg_bank(&c, 4) == 12 && tm_chr_bank(&c, 0) == 16, "38 reg");
    wr(0x6FFF, 0x00); wr(0x8000, 0x00);
    TM_CHECK(tm_prg_bank(&c, 4) == 12, "38 only $7000-$7FFF");
    wr(0x7FFF, 0x05);
    TM_CHECK(tm_prg_bank(&c, 4) == 4 && tm_chr_bank(&c, 0) == 8, "38 $7FFF");
}

static void t_144(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_144, 0, 128, 128, 0, 0, 1), "144 load");
    TM_CHECK(tm_prg_bank(&c, 4) == 0 && tm_chr_bank(&c, 0) == 0, "144 power-on");
    /* PRG is 32K bank 0 -> $8000 is 8K page 0, data byte 0x00 at offset 0 except offset 1 (= 0). */
    wr(0x8000, 0x31);   /* ROM byte 0: effective = 0 & (0x31|1) = 0 */
    TM_CHECK(tm_prg_bank(&c, 4) == 0 && tm_chr_bank(&c, 0) == 0, "144 ROM 0 wins");
    wr(0xE000, 0x30);   /* ROM byte at $E000 = 3: 3 & 0x31 = 1 -> D0 from ROM */
    TM_CHECK(tm_prg_bank(&c, 4) == 4 && tm_chr_bank(&c, 0) == 0, "144 D0 from ROM (prg %u)", tm_prg_bank(&c, 4));
    /* now 32K bank 1: $E000 is 8K page 7 (byte 7): 0xF2 -> 7 & 0xF3 = 3 */
    wr(0xE000, 0xF2);
    TM_CHECK(tm_prg_bank(&c, 4) == 12, "144 ANDed (prg %u)", tm_prg_bank(&c, 4));
}

static void t_193(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_193, 0, 128, 256, 0, 0, 0), "193 load");
    TM_CHECK(tm_prg_bank(&c, 4) == 0 && tm_prg_bank(&c, 5) == 13 && tm_prg_bank(&c, 6) == 14 && tm_prg_bank(&c, 7) == 15, "193 power-on prg");
    TM_CHECK(tm_nt(&c, 1) == 0 && tm_nt(&c, 2) == 1, "193 header H kept");
    TM_CHECK(c.prg_map[3] == NULL, "193 no SRAM");
    wr(0x6000, 0x17);
    TM_CHECK(tm_chr_bank(&c, 0) == 0x14 && tm_chr_bank(&c, 3) == 0x17, "193 $6000 4K");
    wr(0x6001, 0x23);
    TM_CHECK(tm_chr_bank(&c, 4) == 0x22 && tm_chr_bank(&c, 5) == 0x23, "193 $6001 2K");
    wr(0x6002, 0x41);
    TM_CHECK(tm_chr_bank(&c, 6) == 0x40 && tm_chr_bank(&c, 7) == 0x41, "193 $6002 2K");
    wr(0x6003, 0xF5);
    TM_CHECK(tm_prg_bank(&c, 4) == 5 && tm_prg_bank(&c, 5) == 13, "193 $6003 prg");
    wr(0x6004, 0);
    TM_CHECK(tm_nt(&c, 1) == 1 && tm_nt(&c, 2) == 0, "193 V");
    wr(0x7FFC, 1);   /* mask $E007 mirror of $6004 */
    TM_CHECK(tm_nt(&c, 1) == 0 && tm_nt(&c, 2) == 1, "193 H via mirror");
}

static void t_36(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_036, 0, 128, 128, 0, 0, 1), "36 load");
    TM_CHECK(tm_prg_bank(&c, 4) == 0 && tm_chr_bank(&c, 0) == 0, "36 power-on");
    wr(0x4200, 0xF5);
    TM_CHECK(tm_chr_bank(&c, 0) == 40 && tm_chr_bank(&c, 7) == 47, "36 chr");
    TM_CHECK(cart_cpu_read(&c, 0x4100) == 0xC5, "36 read RR=0 (open bus 0xF5 -> %02X)", c.open_bus);
    wr(0x4102, 0x20);   /* PP = 2 */
    wr(0x4100, 0x00);   /* RR = PP */
    c.open_bus = 0x00;
    TM_CHECK(cart_cpu_read(&c, 0x4100) == 0x20, "36 read RR=2");
    c.open_bus = 0xFF;
    TM_CHECK(cart_cpu_read(&c, 0x5100) == 0xEF, "36 read mirror, open bus kept");
    TM_CHECK(tm_prg_bank(&c, 4) == 0, "36 prg waits for $8000 write");
    wr(0x8000, 0x00);
    TM_CHECK(tm_prg_bank(&c, 4) == 8, "36 $8000 RR -> prg");
    wr(0x4101, 0x10);   /* invert */
    wr(0x4100, 0x00);   /* RR = ~2 & 3 = 1 */
    wr(0xFFFF, 0x00);
    TM_CHECK(tm_prg_bank(&c, 4) == 4, "36 invert");
    wr(0x4103, 0x10);   /* increment */
    wr(0x4100, 0x00); wr(0x4100, 0x00); wr(0x4100, 0x00);   /* 1 -> 2 -> 3 -> 0 */
    wr(0x8000, 0x00);
    TM_CHECK(tm_prg_bank(&c, 4) == 0, "36 increment wraps");
    wr(0x4100, 0x00); wr(0x8000, 0x00);
    TM_CHECK(tm_prg_bank(&c, 4) == 4, "36 increment");
    TM_CHECK(tm_chr_bank(&c, 0) == 40, "36 chr unaffected by $4100-$4103");
}

static void t_168(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_168, 0, 64, 0, 64, 0, 1), "168 load");
    TM_CHECK(tm_prg_bank(&c, 4) == 0 && tm_prg_bank(&c, 6) == 6 && tm_prg_bank(&c, 7) == 7, "168 power-on prg");
    /* CHR-RAM: tag pages through the PPU bus */
    wr(0x8000, 0x03);
    cart_ppu_write(&c, 0x1000, 0xA3);
    wr(0x8000, 0x00);
    cart_ppu_write(&c, 0x1000, 0xA0);
    cart_ppu_write(&c, 0x0000, 0x55);
    TM_CHECK(cart_ppu_read(&c, 0x1000) == 0x55, "168 bank 0 at $1000 aliases $0000");
    wr(0x8000, 0xC3);
    TM_CHECK(cart_ppu_read(&c, 0x1000) == 0xA3, "168 bank 3 at $1000");
    TM_CHECK(tm_prg_bank(&c, 4) == 6 && tm_prg_bank(&c, 5) == 7 && tm_prg_bank(&c, 6) == 6, "168 prg 16K bank 3");
    /* protection: banks 8-15 protected at power-on */
    wr(0x8000, 0x09);
    cart_ppu_write(&c, 0x1000, 0x99);
    TM_CHECK(cart_ppu_read(&c, 0x1000) == 0xFF, "168 protected bank reads open bus");
    wr(0xF080, 0xFF); wr(0xF000, 0x00);   /* Z 1 -> 0 clears protection */
    cart_ppu_write(&c, 0x1000, 0x99);
    TM_CHECK(cart_ppu_read(&c, 0x1000) == 0x99, "168 unprotected bank writable");
    wr(0x8000, 0x02);
    TM_CHECK(cart_ppu_read(&c, 0x1000) != 0x99, "168 bank 2 distinct from 9");
    /* the core caps CHR-RAM at 32 KiB, so bank 9 aliases bank 1 here (real board: 64 KiB) */
    wr(0x8000, 0x01);
    TM_CHECK(cart_ppu_read(&c, 0x1000) == (c.chr_size >= 65536 ? cart_ppu_read(&c, 0x1000) : 0x99), "168 bank 1 vs 9 per CHR-RAM size");
    /* IRQ: asserted while the 1024s bit of the free-running M2 counter is set */
    wr(0xC000, 0x04); wr(0xC000, 0x00);
    TM_CHECK(!c.irq_line, "168 irq off after reset");
    for (int i = 0; i < 1023; i++) cart_cpu_cycle(&c);
    TM_CHECK(!c.irq_line, "168 no irq at 1023");
    cart_cpu_cycle(&c);
    TM_CHECK(c.irq_line, "168 irq at 1024");
    for (int i = 0; i < 1023; i++) cart_cpu_cycle(&c);
    TM_CHECK(c.irq_line, "168 irq held to 2047");
    cart_cpu_cycle(&c);
    TM_CHECK(!c.irq_line, "168 self-ack at 2048");
    for (int i = 0; i < 1100; i++) cart_cpu_cycle(&c);
    TM_CHECK(c.irq_line, "168 irq again");
    wr(0xE000, 0x04);
    TM_CHECK(!c.irq_line, "168 ack");
    for (int i = 0; i < 3000; i++) cart_cpu_cycle(&c);
    TM_CHECK(!c.irq_line, "168 held while Z=1");
    wr(0xE000, 0x00);
    for (int i = 0; i < 1024; i++) cart_cpu_cycle(&c);
    TM_CHECK(c.irq_line, "168 restarts from 0");
}

static void rb(uint8_t r, uint8_t v) { wr(0x8000, r); wr(0x8001, v); }
static void t_158(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_158, 0, 128, 256, 0, 0, 0), "158 load");
    TM_CHECK(tm_prg_bank(&c, 4) == 0 && tm_prg_bank(&c, 5) == 1 && tm_prg_bank(&c, 6) == 2 && tm_prg_bank(&c, 7) == 15, "158 power-on prg");
    TM_CHECK(tm_nt(&c, 0) == 0 && tm_nt(&c, 3) == 0, "158 power-on nt from chr regs");
    rb(0, 0x80); rb(1, 0x02);
    TM_CHECK(tm_chr_bank(&c, 0) == 0x80 && tm_chr_bank(&c, 1) == 0x81 && tm_chr_bank(&c, 2) == 2, "158 chr 2K");
    TM_CHECK(tm_nt(&c, 0) == 1 && tm_nt(&c, 1) == 1 && tm_nt(&c, 2) == 0 && tm_nt(&c, 3) == 0, "158 nt from R0/R1 bit 7");
    wr(0xA000, 1);
    TM_CHECK(tm_nt(&c, 0) == 1 && tm_nt(&c, 2) == 0, "158 $A000 ignored");
    rb(0x20, 0x80); rb(0x28, 0x00); rb(0x21, 0x83); rb(0x29, 0x84);   /* K mode: R0,R8,R1,R9 */
    TM_CHECK(tm_nt(&c, 0) == 1 && tm_nt(&c, 1) == 0 && tm_nt(&c, 2) == 1 && tm_nt(&c, 3) == 1, "158 K mode nt");
    rb(0xA2, 0x80); rb(0xA3, 0x00); rb(0xA4, 0x00); rb(0xA5, 0x80);   /* inverted: R2-R5 at $0000 */
    TM_CHECK(tm_chr_bank(&c, 0) == 0x80 && tm_chr_bank(&c, 3) == 0x80, "158 inverted chr");
    TM_CHECK(tm_nt(&c, 0) == 1 && tm_nt(&c, 1) == 0 && tm_nt(&c, 2) == 0 && tm_nt(&c, 3) == 1, "158 inverted nt from R2-R5");
    /* IRQ shared with 64 */
    wr(0xC000, 2); wr(0xC001, 0); wr(0xE001, 0);
    for (int line = 0; line < 8 && !c.irq_line; line++) {
        for (int k = 0; k < 8; k++) cart_ppu_read(&c, 0x0000);
        cart_ppu_read(&c, 0x1000);
        for (int k = 0; k < 8; k++) cart_cpu_cycle(&c);
    }
    TM_CHECK(c.irq_line, "158 A12 irq");
    wr(0xE000, 0);
    TM_CHECK(!c.irq_line, "158 irq ack");

    /* 64 unchanged: $A000 mirroring still works */
    TM_CHECK(tm_load(&c, &mapper_064, 0, 128, 256, 0, 0, 0), "64 load");
    TM_CHECK(tm_nt(&c, 1) == 1 && tm_nt(&c, 2) == 0, "64 power-on V");
    rb(0, 0x80);
    wr(0xA000, 1);
    TM_CHECK(tm_nt(&c, 1) == 0 && tm_nt(&c, 2) == 1 && tm_chr_bank(&c, 0) == 0x80, "64 H, chr");
}

void tm_unl(int *checks, int *fails) {
    t_8259(checks, fails);
    t_148(checks, fails);
    t_38(checks, fails);
    t_144(checks, fails);
    t_193(checks, fails);
    t_36(checks, fails);
    t_168(checks, fails);
    t_158(checks, fails);
}
