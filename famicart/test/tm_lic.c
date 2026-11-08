/* Tests for the licensed-board ports (src/core/mappers/m_port_lic.c) and Bandai Datach (157, m016_bandai.c). */
#include "tm_util.h"
#include "mappers/mmc1.h"

extern const mapper_desc_t mapper_077, mapper_096, mapper_101, mapper_105, mapper_157, mapper_186, mapper_188, mapper_006;

static cart_t c;

static bool chr_is(const cart_t *cc, unsigned slot, uint32_t bank1k) { return cc->chr_map[slot] == cc->chr + bank1k * 1024u; }
static uint8_t rd(uint16_t a) { return cart_cpu_read(&c, a); }
static void wr(uint16_t a, uint8_t v) { cart_cpu_write(&c, a, v); }
static void clock_n(unsigned n) { for (unsigned i = 0; i < n; i++) cart_cpu_cycle(&c); }

/* ---- 77 ---- */
static void t77(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_077, 0, 512, 32, 0, 0, 2), "77 load");
    TM_CHECK(tm_prg_bank(&c, 4) == 0 && tm_prg_bank(&c, 7) == 3, "77 power-on PRG");
    TM_CHECK(tm_chr_bank(&c, 0) == 0 && tm_chr_bank(&c, 1) == 1, "77 power-on CHR");
    wr(0x8000, 0x35);
    TM_CHECK(tm_prg_bank(&c, 4) == 20 && tm_prg_bank(&c, 7) == 23, "77 PRG 32K bank 5: %u", tm_prg_bank(&c, 4));
    TM_CHECK(tm_chr_bank(&c, 0) == 6 && tm_chr_bank(&c, 1) == 7, "77 CHR 2K bank 3");
    wr(0xFFFF, 0xF2);
    TM_CHECK(tm_prg_bank(&c, 4) == 8 && tm_chr_bank(&c, 0) == 30, "77 PRG 2 / CHR 15");
    /* CHR-RAM $0800-$1FFF */
    cart_ppu_write(&c, 0x0800, 0x5A); cart_ppu_write(&c, 0x1FFF, 0xA5);
    TM_CHECK(cart_ppu_read(&c, 0x0800) == 0x5A && cart_ppu_read(&c, 0x1FFF) == 0xA5, "77 CHR-RAM");
    cart_ppu_write(&c, 0x0000, 0x77);
    TM_CHECK(cart_ppu_read(&c, 0x0000) == 30, "77 CHR-ROM not writable");
    wr(0x8000, 0x00);
    TM_CHECK(cart_ppu_read(&c, 0x0800) == 0x5A, "77 CHR-RAM unaffected by banking");
    /* nametables: $2000/$2400 cartridge RAM, $2800/$2C00 CIRAM 0/1 */
    TM_CHECK(tm_nt(&c, 0) == -1 && tm_nt(&c, 1) == -1 && tm_nt(&c, 2) == 0 && tm_nt(&c, 3) == 1, "77 NT layout");
    cart_ppu_write(&c, 0x2000, 0x11); cart_ppu_write(&c, 0x2400, 0x22);
    TM_CHECK(cart_ppu_read(&c, 0x2000) == 0x11 && cart_ppu_read(&c, 0x2400) == 0x22, "77 NT RAM");
    TM_CHECK(c.prg_map[3] == NULL, "77 no WRAM");
    /* non-four-screen header falls back to the static NT RAM */
    TM_CHECK(tm_load(&c, &mapper_077, 0, 128, 32, 0, 0, 0), "77 load H");
    TM_CHECK(tm_nt(&c, 0) == -1 && tm_nt(&c, 1) == -1 && tm_nt(&c, 2) == 0 && tm_nt(&c, 3) == 1, "77 NT layout (H header)");
}

/* ---- 96 ---- */
static void t96(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_096, 0, 128, 0, 32, 0, 1), "96 load");
    TM_CHECK(tm_prg_bank(&c, 4) == 0 && chr_is(&c, 0, 0) && chr_is(&c, 4, 12), "96 power-on");
    wr(0x8000, 0x07);
    TM_CHECK(tm_prg_bank(&c, 4) == 12 && tm_prg_bank(&c, 7) == 15, "96 PRG bank 3");
    TM_CHECK(chr_is(&c, 0, 16) && chr_is(&c, 4, 28), "96 outer CHR 1");
    cart_ppu_read(&c, 0x0000); cart_ppu_read(&c, 0x2200);
    TM_CHECK(chr_is(&c, 0, 24) && chr_is(&c, 3, 27) && chr_is(&c, 4, 28), "96 NT fetch $22xx -> inner 2");
    cart_ppu_read(&c, 0x23C0);   /* attribute fetch right after: no re-latch */
    TM_CHECK(chr_is(&c, 0, 24), "96 attribute fetch keeps latch");
    cart_ppu_read(&c, 0x1000); cart_ppu_read(&c, 0x2100);
    TM_CHECK(chr_is(&c, 0, 20), "96 NT fetch $21xx -> inner 1");
    cart_ppu_read(&c, 0x0000); cart_ppu_read(&c, 0x3300);
    TM_CHECK(chr_is(&c, 0, 20), "96 $3xxx does not latch");
    cart_ppu_read(&c, 0x2F00);   /* $3xxx -> $2xxx latches (A9-A8 = 3) */
    TM_CHECK(chr_is(&c, 0, 28), "96 $3xxx -> $2Fxx latches 3");
    wr(0x8000, 0x01);
    TM_CHECK(tm_prg_bank(&c, 4) == 4 && chr_is(&c, 0, 12) && chr_is(&c, 4, 12), "96 outer 0 keeps inner");
    cart_ppu_read(&c, 0x0000); cart_ppu_read(&c, 0x2000);
    TM_CHECK(chr_is(&c, 0, 0), "96 NT fetch $20xx -> inner 0");
    TM_CHECK(tm_nt(&c, 1) == 1 && tm_nt(&c, 2) == 0, "96 vertical");
}

/* ---- 101 ---- */
static void t101(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_101, 0, 32, 64, 0, 8, 0), "101 load");
    TM_CHECK(tm_prg_bank(&c, 4) == 0 && tm_prg_bank(&c, 7) == 3 && tm_chr_bank(&c, 0) == 0, "101 power-on");
    TM_CHECK(c.prg_map[3] == NULL, "101 no WRAM");
    wr(0x6000, 5);
    TM_CHECK(tm_chr_bank(&c, 0) == 40 && tm_chr_bank(&c, 7) == 47, "101 CHR 5");
    wr(0x7FFF, 2);
    TM_CHECK(tm_chr_bank(&c, 0) == 16, "101 CHR 2 (bits not swapped)");
    wr(0x8000, 7);
    TM_CHECK(tm_chr_bank(&c, 0) == 16 && tm_prg_bank(&c, 4) == 0, "101 $8000 ignored");
    TM_CHECK(tm_nt(&c, 1) == 0 && tm_nt(&c, 2) == 1, "101 header mirroring");
}

/* ---- 105 ---- */
/* mirror of the private nwc_state_t in m_port_lic.c (to fast-forward the 30-bit timer) */
typedef struct { mmc1_state_t m; uint8_t lock; uint8_t last_i; uint32_t counter; } nwc_mirror_t;
static void mmc1w(uint16_t a, uint8_t v) {
    for (int i = 0; i < 5; i++) { c.cpu_cycles += 2; wr(a, (uint8_t)((v >> i) & 1)); }
}
static void t105(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_105, 0, 256, 0, 8, 8, 0), "105 load");
    TM_CHECK(tm_prg_bank(&c, 4) == 0 && tm_prg_bank(&c, 7) == 3, "105 power-on first 32K");
    mmc1w(0xA000, 0x04);   /* I=0, AA=2: still locked */
    TM_CHECK(tm_prg_bank(&c, 4) == 0, "105 locked");
    mmc1w(0xE000, 0x05); mmc1w(0x8000, 0x0F);
    TM_CHECK(tm_prg_bank(&c, 4) == 0 && tm_prg_bank(&c, 6) == 2, "105 locked ignores MMC1 PRG");
    mmc1w(0xA000, 0x14);   /* I 0 -> 1 unlocks */
    TM_CHECK(tm_prg_bank(&c, 4) == 8 && tm_prg_bank(&c, 7) == 11, "105 unlocked, A = 2: %u", tm_prg_bank(&c, 4));
    TM_CHECK(tm_nt(&c, 1) == 0 && tm_nt(&c, 2) == 1, "105 MMC1 mirroring H");
    mmc1w(0xA000, 0x02);
    TM_CHECK(tm_prg_bank(&c, 4) == 4, "105 A = 1");
    /* O = 1: second chip, MMC1 modes */
    mmc1w(0x8000, 0x0C); mmc1w(0xE000, 0x03); mmc1w(0xA000, 0x18);
    TM_CHECK(tm_prg_bank(&c, 4) == 22 && tm_prg_bank(&c, 6) == 30, "105 O=1 P=1 S=1: %u %u", tm_prg_bank(&c, 4), tm_prg_bank(&c, 6));
    mmc1w(0x8000, 0x08);
    TM_CHECK(tm_prg_bank(&c, 4) == 16 && tm_prg_bank(&c, 6) == 22, "105 O=1 P=1 S=0");
    mmc1w(0x8000, 0x00);
    TM_CHECK(tm_prg_bank(&c, 4) == 20 && tm_prg_bank(&c, 7) == 23, "105 O=1 P=0 (32K)");
    mmc1w(0x8000, 0x02);
    TM_CHECK(tm_nt(&c, 1) == 1 && tm_nt(&c, 2) == 0, "105 MMC1 mirroring V");
    /* WRAM + W bit */
    mmc1w(0xE000, 0x03);
    wr(0x6000, 0x42); TM_CHECK(rd(0x6000) == 0x42, "105 WRAM");
    mmc1w(0xE000, 0x13); TM_CHECK(c.prg_map[3] == NULL, "105 WRAM disabled");
    mmc1w(0xE000, 0x03);
    TM_CHECK(chr_is(&c, 0, 0) && chr_is(&c, 7, 7), "105 CHR-RAM fixed");
    /* IRQ: timer is held at 0 while I=1 */
    nwc_mirror_t *s = (nwc_mirror_t *)c.s.raw;
    mmc1w(0xA000, 0x10);
    clock_n(100);
    TM_CHECK(s->counter == 0 && !c.irq_line, "105 timer held while I=1");
    mmc1w(0xA000, 0x00);
    clock_n(10);
    TM_CHECK(s->counter > 0 && s->counter <= 20, "105 timer runs while I=0 (%u)", (unsigned)s->counter);
    s->counter = 0x28000000u - 3;   /* tournament DIP: $28000000 M2 cycles (6:14) */
    clock_n(2); TM_CHECK(!c.irq_line, "105 no IRQ before $28000000");
    clock_n(1); TM_CHECK(c.irq_line, "105 IRQ at $28000000");
    clock_n(5); TM_CHECK(c.irq_line, "105 IRQ stays pending");
    mmc1w(0xA000, 0x10);
    TM_CHECK(!c.irq_line && s->counter == 0, "105 I=1 acknowledges and resets");
}

/* ---- 157 ---- */
static void ee_set(bool ext, int scl, int sda) {
    if (!ext) wr(0x800D, (uint8_t)((sda << 6) | (scl << 5)));
    else { wr(0x800D, (uint8_t)(sda << 6)); wr(0x8000, (uint8_t)(scl << 3)); }
}
static int ee_sda(void) { return (rd(0x6000) >> 4) & 1; }
static void ee_start(bool ext) { ee_set(ext, 0, 1); ee_set(ext, 1, 1); ee_set(ext, 1, 0); ee_set(ext, 0, 0); }
static void ee_stop(bool ext) { ee_set(ext, 0, 0); ee_set(ext, 1, 0); ee_set(ext, 1, 1); }
static int ee_wbyte(bool ext, uint8_t b) {
    for (int i = 7; i >= 0; i--) { int d = (b >> i) & 1; ee_set(ext, 0, d); ee_set(ext, 1, d); ee_set(ext, 0, d); }
    ee_set(ext, 0, 1); ee_set(ext, 1, 1); int ack = !ee_sda(); ee_set(ext, 0, 1);
    return ack;
}
static uint8_t ee_rbyte(bool ext, bool ack) {
    uint8_t b = 0;
    for (int i = 0; i < 8; i++) { ee_set(ext, 0, 1); ee_set(ext, 1, 1); b = (uint8_t)((b << 1) | ee_sda()); }
    ee_set(ext, 0, ack ? 0 : 1); ee_set(ext, 1, ack ? 0 : 1); ee_set(ext, 0, ack ? 0 : 1);
    return b;
}
static void t157(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_157, 0, 256, 0, 8, 1, 1), "157 load");
    TM_CHECK(tm_prg_bank(&c, 4) == 0 && tm_prg_bank(&c, 6) == 30 && tm_prg_bank(&c, 7) == 31, "157 power-on");
    TM_CHECK(c.prg_map[3] == NULL, "157 no WRAM at $6000");
    wr(0x8008, 3); TM_CHECK(tm_prg_bank(&c, 4) == 6 && tm_prg_bank(&c, 6) == 30, "157 PRG 3");
    wr(0xC008, 4); TM_CHECK(tm_prg_bank(&c, 4) == 8, "157 PRG mirror $C008");
    wr(0x6008, 1); TM_CHECK(tm_prg_bank(&c, 4) == 8, "157 $6000 writes ignored");
    wr(0x8009, 0); TM_CHECK(tm_nt(&c, 1) == 1 && tm_nt(&c, 2) == 0, "157 mirroring V");
    wr(0x8009, 1); TM_CHECK(tm_nt(&c, 1) == 0 && tm_nt(&c, 2) == 1, "157 mirroring H");
    wr(0x8009, 2); TM_CHECK(tm_nt(&c, 0) == 0 && tm_nt(&c, 3) == 0, "157 1-screen A");
    wr(0x8009, 3); TM_CHECK(tm_nt(&c, 0) == 1 && tm_nt(&c, 3) == 1, "157 1-screen B");
    for (int i = 0; i < 8; i++) wr((uint16_t)(0x8000 + i), (uint8_t)(i + 1));
    TM_CHECK(chr_is(&c, 0, 0) && chr_is(&c, 7, 7), "157 CHR-RAM unbanked");
    /* barcode reader idle, EEPROM line released */
    c.open_bus = 0xFF; TM_CHECK((cart_cpu_read(&c, 0x6000) & 0x18) == 0x10, "157 read: SDA=1 barcode=0");
    c.open_bus = 0x00; TM_CHECK((cart_cpu_read(&c, 0x7FFF) & 0xFF) == 0x10, "157 read: other bits open bus");
    /* IRQ: latch 5 -> fires on the 6th M2 */
    wr(0x800B, 5); wr(0x800C, 0); wr(0x800A, 1);
    clock_n(5); TM_CHECK(!c.irq_line, "157 no IRQ yet");
    clock_n(1); TM_CHECK(c.irq_line, "157 IRQ");
    wr(0x800A, 0); TM_CHECK(!c.irq_line, "157 IRQ ack");
    clock_n(100); TM_CHECK(!c.irq_line, "157 IRQ disabled");
    /* internal 24C02: write $5A to address $12, read it back */
    ee_stop(false);
    ee_start(false);
    TM_CHECK(ee_wbyte(false, 0xA0) && ee_wbyte(false, 0x12) && ee_wbyte(false, 0x5A), "157 24C02 write acks");
    ee_stop(false);
    TM_CHECK(c.wram[0x12] == 0x5A, "157 24C02 saved to WRAM");
    ee_start(false);
    TM_CHECK(ee_wbyte(false, 0xA0) && ee_wbyte(false, 0x12), "157 24C02 set address");
    ee_start(false);
    TM_CHECK(ee_wbyte(false, 0xA1), "157 24C02 read select");
    TM_CHECK(ee_rbyte(false, false) == 0x5A, "157 24C02 read back");
    ee_stop(false);
    /* external 24C01 (Battle Rush): SCL on $8000 bit 3, SDA shared */
    ee_stop(true);
    ee_start(true);
    TM_CHECK(ee_wbyte(true, (uint8_t)(0x05 << 1)) && ee_wbyte(true, 0xC3), "157 24C01 write acks");
    ee_stop(true);
    TM_CHECK(c.wram[256 + 5] == 0xC3, "157 24C01 saved to WRAM+256");
    TM_CHECK(c.wram[5] == 0x00, "157 internal EEPROM untouched (loader zeroed WRAM)");
    ee_start(true);
    TM_CHECK(ee_wbyte(true, (uint8_t)((0x05 << 1) | 1)), "157 24C01 read select");
    TM_CHECK(ee_rbyte(true, false) == 0xC3, "157 24C01 read back");
    ee_stop(true);
    /* EEPROM contents restored from WRAM on power-on */
    TM_CHECK(tm_load(&c, &mapper_157, 0, 128, 0, 8, 1, 1), "157 reload");
    c.wram[0x20] = 0xAB; c.wram[256 + 7] = 0xCD;
    TM_CHECK(mapper_attach_desc(&c, &mapper_157, 0), "157 re-attach");
    ee_start(false); ee_wbyte(false, 0xA0); ee_wbyte(false, 0x20); ee_start(false); ee_wbyte(false, 0xA1);
    TM_CHECK(ee_rbyte(false, false) == 0xAB, "157 24C02 restored from WRAM"); ee_stop(false);
    ee_start(true); ee_wbyte(true, (uint8_t)((7 << 1) | 1));
    TM_CHECK(ee_rbyte(true, false) == 0xCD, "157 24C01 restored from WRAM+256"); ee_stop(true);
    /* no external EEPROM without Battle Rush's WRAM size: its SCL writes do nothing */
    TM_CHECK(tm_load(&c, &mapper_157, 0, 128, 0, 8, 1, 1), "157 load 256B");
    c.wram_size = 256; TM_CHECK(mapper_attach_desc(&c, &mapper_157, 0), "157 attach with 256 bytes of WRAM");
    ee_start(true);
    TM_CHECK(!ee_wbyte(true, 0x0A), "157 no external EEPROM: no ACK");
}

/* ---- 186 ---- */
static void t186(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_186, 0, 256, 0, 8, 32, 2), "186 load");
    TM_CHECK(tm_prg_bank(&c, 4) == 0 && tm_prg_bank(&c, 6) == 0 && tm_prg_bank(&c, 7) == 1, "186 power-on");
    wr(0x4201, 5);
    TM_CHECK(tm_prg_bank(&c, 4) == 10 && tm_prg_bank(&c, 5) == 11 && tm_prg_bank(&c, 6) == 0, "186 PRG 5, $C000 fixed 0");
    wr(0x4201, 0x1F); TM_CHECK(tm_prg_bank(&c, 4) == 30, "186 PRG 15");
    TM_CHECK(c.prg_map[3] == c.wram + 16384, "186 RAM-B page 0");
    wr(0x4200, 0x40); TM_CHECK(c.prg_map[3] == c.wram + 24576, "186 RAM-B page 1");
    wr(0x6000, 0x99); TM_CHECK(rd(0x6000) == 0x99, "186 RAM-B r/w");
    wr(0x4200, 0x00);
    wr(0x4400, 0x11); TM_CHECK(rd(0x4400) == 0x11 && rd(0x5400) == 0x11, "186 $4400 = RAM-A page 0");
    wr(0x5000, 0x22); wr(0x4200, 0x01); wr(0x5000, 0x33);
    TM_CHECK(rd(0x5000) == 0x33 && rd(0x4400) == 0x11, "186 RAM-A page 1");
    wr(0x4200, 0x00); TM_CHECK(rd(0x5000) == 0x22, "186 RAM-A page 0 kept");
    wr(0x4200, 0x03); wr(0x5FFF, 0x44); TM_CHECK(rd(0x5FFF) == 0x44, "186 RAM-A page 3");
    TM_CHECK(rd(0x4200) == 0x00 && rd(0x4201) == 0x80 && rd(0x4202) == 0x00, "186 tape absent");
    TM_CHECK(tm_nt(&c, 2) == -1 && tm_nt(&c, 3) == -1, "186 four-screen");
    clock_n(1000); TM_CHECK(!c.irq_line, "186 no IRQ");
}

/* ---- 188 ---- */
static void t188(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_188, 0, 256, 0, 8, 0, 1), "188 load");
    TM_CHECK(tm_prg_bank(&c, 4) == 16 && tm_prg_bank(&c, 6) == 14 && tm_prg_bank(&c, 7) == 15, "188 power-on (expansion 0)");
    wr(0x8000, 0x13); TM_CHECK(tm_prg_bank(&c, 4) == 6, "188 internal 3");
    wr(0x8000, 0x1F); TM_CHECK(tm_prg_bank(&c, 4) == 14, "188 internal 15 -> 7");
    wr(0x8000, 0x05); TM_CHECK(tm_prg_bank(&c, 4) == 26 && tm_prg_bank(&c, 6) == 14, "188 expansion 5");
    TM_CHECK(tm_nt(&c, 1) == 1 && tm_nt(&c, 2) == 0, "188 X=0 vertical");
    wr(0x8000, 0x30); TM_CHECK(tm_nt(&c, 1) == 0 && tm_nt(&c, 2) == 1 && tm_prg_bank(&c, 4) == 0, "188 X=1 horizontal");
    c.open_bus = 0xF0; TM_CHECK(cart_cpu_read(&c, 0x6000) == 0xF3, "188 buttons released, mic silent");
    TM_CHECK(tm_load(&c, &mapper_188, 0, 128, 0, 8, 0, 1), "188 load 128K");
    TM_CHECK(c.prg_map[4] == NULL && c.prg_map[5] == NULL && tm_prg_bank(&c, 6) == 14, "188 no expansion: open bus");
    c.open_bus = 0x5C; TM_CHECK(cart_cpu_read(&c, 0x8000) == 0x5C, "188 open bus read");
    wr(0x8000, 0x12); TM_CHECK(tm_prg_bank(&c, 4) == 4, "188 internal 2 (128K)");
}

/* ---- 6 ---- */
static void t006(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_006, 0, 256, 0, 32, 32, 1), "6 load");
    TM_CHECK(tm_prg_bank(&c, 4) == 0 && tm_prg_bank(&c, 6) == 14 && chr_is(&c, 0, 0), "6 power-on (mode 1)");
    TM_CHECK(tm_nt(&c, 1) == 1 && tm_nt(&c, 2) == 0, "6 power-on vertical");
    TM_CHECK(c.prg_map[3] == c.wram, "6 WRAM bank 0");
    wr(0x8000, 0x0E);
    TM_CHECK(tm_prg_bank(&c, 4) == 6 && tm_prg_bank(&c, 6) == 14 && chr_is(&c, 0, 16) && c.chr_wmask == 0xFF, "6 mode 1 latch");
    wr(0xFFFF, 0x3C); TM_CHECK(tm_prg_bank(&c, 4) == 30, "6 mode 1 PRG 15");
    wr(0x42FE, 0x10);   /* mode 0, one-screen page 1, protected */
    TM_CHECK(tm_nt(&c, 0) == 1 && tm_nt(&c, 2) == 1, "6 one-screen 1");
    wr(0x8000, 0x0E); TM_CHECK(tm_prg_bank(&c, 4) == 12 && tm_prg_bank(&c, 6) == 14 && chr_is(&c, 0, 0), "6 mode 0");
    wr(0x42FC, 0x00); TM_CHECK(tm_nt(&c, 0) == 0 && tm_nt(&c, 3) == 0, "6 one-screen 0");
    wr(0x8000, 0x07); TM_CHECK(tm_prg_bank(&c, 4) == 12, "6 latch disabled when A1=0");
    wr(0x42FF, 0x40); wr(0x8000, 0x0B);
    TM_CHECK(tm_prg_bank(&c, 4) == 22 && tm_prg_bank(&c, 6) == 30, "6 mode 2");
    wr(0x42FF, 0x70); wr(0x8000, 0x25);
    TM_CHECK(tm_prg_bank(&c, 4) == 30 && tm_prg_bank(&c, 6) == 10 && chr_is(&c, 0, 16), "6 mode 3");
    TM_CHECK(tm_nt(&c, 1) == 0 && tm_nt(&c, 2) == 1, "6 two-screen horizontal");
    wr(0x42FF, 0x80); wr(0x8000, 0x31);
    TM_CHECK(tm_prg_bank(&c, 4) == 12 && tm_prg_bank(&c, 7) == 15 && chr_is(&c, 0, 8) && c.chr_wmask == 0, "6 mode 4 GNROM, CHR protected");
    wr(0x42FF, 0xA0); wr(0x8000, 0x02); TM_CHECK(tm_prg_bank(&c, 4) == 12 && chr_is(&c, 0, 16), "6 mode 5");
    wr(0x42FF, 0xC0); wr(0x8000, 0x03); TM_CHECK(tm_prg_bank(&c, 4) == 12 && chr_is(&c, 0, 8), "6 mode 6");
    wr(0x42FF, 0xE0); wr(0x8000, 0x03); TM_CHECK(tm_prg_bank(&c, 4) == 12 && chr_is(&c, 0, 0) && c.chr_wmask == 0, "6 mode 7");
    cart_ppu_write(&c, 0x0000, 0x77); TM_CHECK(cart_ppu_read(&c, 0x0000) != 0x77, "6 CHR write-protected");
    wr(0x42FF, 0x20);
    cart_ppu_write(&c, 0x0000, 0x77); TM_CHECK(cart_ppu_read(&c, 0x0000) == 0x77, "6 CHR writable in mode 1");
    /* M2 IRQ */
    wr(0x4502, 0xFD); wr(0x4503, 0xFF);
    clock_n(2); TM_CHECK(!c.irq_line, "6 no IRQ before wrap");
    clock_n(1); TM_CHECK(c.irq_line, "6 IRQ on $FFFF -> $0000");
    wr(0x4502, 0x00); TM_CHECK(!c.irq_line, "6 $4502 acknowledges");
    wr(0x4501, 0); wr(0x4502, 0xFF); wr(0x4503, 0xFF); wr(0x4501, 0);
    clock_n(10); TM_CHECK(!c.irq_line, "6 $4501 stops counting");
    /* PA12 IRQ */
    wr(0x4500, 0x4A); wr(0x4502, 0xFE); wr(0x4503, 0xFF);
    clock_n(10); TM_CHECK(!c.irq_line, "6 PA12 mode ignores M2");
    cart_ppu_read(&c, 0x0000); cart_ppu_read(&c, 0x1000); cart_ppu_read(&c, 0x1008);
    TM_CHECK(!c.irq_line, "6 one A12 rise");
    cart_ppu_read(&c, 0x0000); cart_ppu_read(&c, 0x1000);
    TM_CHECK(c.irq_line, "6 IRQ after two A12 rises");
    wr(0x4501, 0);
    /* $4500: WRAM bank, 1K CHR mode, nametables from CHR */
    wr(0x4500, 0x62); TM_CHECK(c.prg_map[3] == c.wram + 2 * 8192, "6 WRAM bank 2");
    for (int i = 0; i < 8; i++) wr((uint16_t)(0x4510 + i), (uint8_t)(20 + i));
    wr(0x4500, 0x43); TM_CHECK(chr_is(&c, 0, 20) && chr_is(&c, 7, 27), "6 1K CHR mode");
    wr(0x4518, 5); wr(0x4519, 6); wr(0x451A, 7); wr(0x451B, 8);
    wr(0x4500, 0x40); TM_CHECK(c.nt_map[0] == c.chr + 5 * 1024 && c.nt_map[3] == c.chr + 8 * 1024 && chr_is(&c, 0, 24), "6 NT from CHR");
    wr(0x4500, 0x42); TM_CHECK(tm_nt(&c, 0) == 0 && tm_nt(&c, 1) == 1 && tm_nt(&c, 2) == 0, "6 NT back to CIRAM (V)");
    /* NES 2.0 submapper selects the power-on mode */
    TM_CHECK(tm_load(&c, &mapper_006, 4, 128, 32, 0, 0, 0), "6 load sub 4");
    TM_CHECK(tm_prg_bank(&c, 4) == 0 && tm_nt(&c, 1) == 0 && tm_nt(&c, 2) == 1, "6 sub 4 power-on (GNROM, H)");
    wr(0x8000, 0x13); TM_CHECK(tm_prg_bank(&c, 4) == 4 && tm_chr_bank(&c, 0) == 24, "6 sub 4 GNROM latch, CHR-ROM");
}

void tm_lic(int *checks, int *fails) {
    t77(checks, fails); t96(checks, fails); t101(checks, fails); t105(checks, fails);
    t157(checks, fails); t186(checks, fails); t188(checks, fails); t006(checks, fails);
}
