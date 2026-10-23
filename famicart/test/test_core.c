/* Host-side unit tests for the portable core. Build: see test/Makefile. */
#include "../src/core/cartload.h"
#include "../src/core/mapper.h"
#include "../src/core/rom.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int fails = 0, checks = 0;
#define CHECK(cond, ...) do { checks++; if (!(cond)) { fails++; printf("FAIL %s:%d: ", __FILE__, __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

static uint8_t *make_ines(uint32_t prg, uint32_t chr, uint16_t mapper, uint8_t sub, bool nes2, uint32_t *len) {
    *len = 16 + prg + chr; uint8_t *p = calloc(1, *len);
    memcpy(p, "NES\x1a", 4); p[4] = (uint8_t)(prg / 16384); p[5] = (uint8_t)(chr / 8192);
    p[6] = (uint8_t)((mapper & 0x0F) << 4) | 1; p[7] = (uint8_t)(mapper & 0xF0) | (nes2 ? 0x08 : 0);
    if (nes2) { p[8] = (uint8_t)(((mapper >> 8) & 0x0F) | (sub << 4)); p[10] = 0x70; }
    /* fill PRG with page markers: byte[i] = page index of 8K page */
    for (uint32_t i = 0; i < prg; i++) p[16 + i] = (uint8_t)(i >> 13);
    for (uint32_t i = 0; i < chr; i++) p[16 + prg + i] = (uint8_t)(0x80 | (i >> 10));
    return p;
}

static void test_crc(void) {
    CHECK(fc_crc32(0, (const uint8_t *)"123456789", 9) == 0xCBF43926, "crc32 known answer");
    uint8_t all[256]; for (int k = 0; k < 256; k++) all[k] = (uint8_t)k;
    CHECK(fc_crc32(0, all, 256) == 0x29058C73, "crc32 over 0x00..0xFF = %08X", fc_crc32(0, all, 256));
    CHECK(fc_crc32(fc_crc32(0, all, 100), all + 100, 156) == 0x29058C73, "crc32 incremental");
}
static void test_header(void) {
    uint32_t len; uint8_t *img = make_ines(32768, 8192, 4, 0, false, &len);
    rom_info_t i; CHECK(rom_inspect(img, len, &i), "inspect ines");
    CHECK(i.mapper == 4 && i.prg_size == 32768 && i.chr_size == 8192 && i.mirroring == 1, "ines fields m=%u", i.mapper);
    free(img);
    img = make_ines(131072, 0, 0x115 /*277*/, 3, true, &len);
    CHECK(rom_inspect(img, len, &i) && i.source == ROM_SRC_NES20 && i.mapper == 277 && i.submapper == 3 && i.sram_size == 8192 && i.wram_size == 0, "nes2 fields m=%u sub=%u sram=%u", i.mapper, i.submapper, (unsigned)i.sram_size);
    free(img);
    /* dirty iNES header: upper mapper nibble ignored */
    img = make_ines(32768, 8192, 0xF1, 0, false, &len); img[12] = 'D'; img[13] = 'i';
    CHECK(rom_inspect(img, len, &i) && i.mapper == 1, "dirty header m=%u", i.mapper);
    free(img);
    /* headerless 40K => NROM-256 guess */
    uint8_t *raw = calloc(1, 40960); CHECK(rom_inspect(raw, 40960, &i) && i.source == ROM_SRC_HEURISTIC && i.mapper == 0 && i.prg_size == 32768, "headerless guess"); free(raw);
}
static void test_db(void) {
    extern const void *romdb_lookup(uint32_t);
    #include "../src/core/romdb_gen.h"
    const romdb_entry_t *e = romdb_lookup(romdb_table[ROMDB_COUNT / 2].crc);
    CHECK(e && e->crc == romdb_table[ROMDB_COUNT / 2].crc && e->mapper == romdb_table[ROMDB_COUNT / 2].mapper, "db binary search mid");
    e = romdb_lookup(romdb_table[0].crc); CHECK(e && e->crc == romdb_table[0].crc, "db first");
    e = romdb_lookup(romdb_table[ROMDB_COUNT - 1].crc); CHECK(e && e->crc == romdb_table[ROMDB_COUNT - 1].crc, "db last");
    CHECK(romdb_lookup(0x12345679) == NULL || ((const romdb_entry_t *)romdb_lookup(0x12345679))->crc == 0x12345679, "db miss");
    for (int i = 1; i < ROMDB_COUNT; i++) if (romdb_table[i - 1].crc >= romdb_table[i].crc) { CHECK(false, "db not sorted at %d", i); break; }
}
static cart_t C;
static void test_mmc1(void) {
    uint32_t len; uint8_t *img = make_ines(262144, 0, 1, 0, false, &len);
    rom_info_t i; CHECK(cart_load(&C, img, len, NULL, &i) == LOAD_OK, "load mmc1");
    CHECK(cart_cpu_read(&C, 0x8000) == 0 && cart_cpu_read(&C, 0xC000) == 30, "mmc1 power-on banks %u %u", cart_cpu_read(&C, 0x8000), cart_cpu_read(&C, 0xC000));
    /* write PRG reg = 5 (5 serial writes, LSB first) */
    uint8_t v = 5; for (int k = 0; k < 5; k++) { C.cpu_cycles += 2; cart_cpu_write(&C, 0xE000, (v >> k) & 1); }
    CHECK(cart_cpu_read(&C, 0x8000) == 10 && cart_cpu_read(&C, 0xA000) == 11 && cart_cpu_read(&C, 0xC000) == 30, "mmc1 prg switch -> %u", cart_cpu_read(&C, 0x8000));
    /* consecutive-cycle write ignored */
    C.cpu_cycles += 2; cart_cpu_write(&C, 0xE000, 0x80); C.cpu_cycles += 1; cart_cpu_write(&C, 0xE000, 0x00);
    CHECK(C.s.mmc1.count == 0, "mmc1 reset + ignored consecutive write");
    /* CHR-RAM write/read */
    cart_ppu_write(&C, 0x0123, 0x5A); CHECK(cart_ppu_read(&C, 0x0123) == 0x5A, "chr-ram rw");
    /* WRAM */
    cart_cpu_write(&C, 0x6000, 0x77); CHECK(cart_cpu_read(&C, 0x6000) == 0x77, "wram rw");
    free(img);
}
static void test_mmc3(void) {
    uint32_t len; uint8_t *img = make_ines(131072, 131072, 4, 0, false, &len);
    rom_info_t i; CHECK(cart_load(&C, img, len, NULL, &i) == LOAD_OK, "load mmc3");
    CHECK(cart_cpu_read(&C, 0xE000) == 15 && cart_cpu_read(&C, 0xC000) == 14, "mmc3 fixed banks");
    cart_cpu_write(&C, 0x8000, 6); cart_cpu_write(&C, 0x8001, 3); CHECK(cart_cpu_read(&C, 0x8000) == 3, "mmc3 prg r6");
    cart_cpu_write(&C, 0x8000, 0x46); cart_cpu_write(&C, 0x8001, 3); CHECK(cart_cpu_read(&C, 0xC000) == 3 && cart_cpu_read(&C, 0x8000) == 14, "mmc3 prg mode 1");
    cart_cpu_write(&C, 0x8000, 2); cart_cpu_write(&C, 0x8001, 0x21); CHECK(cart_ppu_read(&C, 0x1000) == (0x80 | 0x21), "mmc3 chr r2 -> %02X", cart_ppu_read(&C, 0x1000));
    cart_cpu_write(&C, 0x8000, 0x80 | 2); CHECK(cart_ppu_read(&C, 0x0000) == (0x80 | 0x21), "mmc3 chr inversion");
    /* IRQ: latch 2, reload, enable; 3 A12 rising edges => IRQ */
    cart_cpu_write(&C, 0xC000, 2); cart_cpu_write(&C, 0xC001, 0); cart_cpu_write(&C, 0xE001, 0);
    for (int e = 0; e < 3; e++) { for (int k = 0; k < 8; k++) cart_ppu_read(&C, 0x0000); cart_ppu_read(&C, 0x1000); }
    CHECK(C.irq_line == 1, "mmc3 irq fired after 3 edges (counter=%u)", C.s.mmc3.irq_counter);
    cart_cpu_write(&C, 0xE000, 0); CHECK(C.irq_line == 0, "mmc3 irq ack");
    cart_cpu_write(&C, 0xA000, 1); CHECK(C.mirroring == MIRROR_H && C.nt_ciram_a10[2] == 1 && C.nt_ciram_a10[1] == 0, "mmc3 mirroring H");
    free(img);
}
static void test_mmc5_profile_vrc7(void) {
    uint32_t len; uint8_t *img = make_ines(131072, 131072, 5, 0, false, &len);
    cart_profile_t p; profile_default(&p);
    p.audio[0].chip = AUDIO_VRC7; p.audio[0].exclusive = 1; p.audio[1].chip = AUDIO_MMC5;
    p.crc = fc_crc32(0, (const uint8_t *)&p, offsetof(cart_profile_t, crc));
    rom_info_t i; CHECK(cart_load(&C, img, len, &p, &i) == LOAD_OK, "load mmc5+vrc7");
    CHECK(C.audio_mask & (1u << AUDIO_VRC7), "vrc7 audio enabled on mmc5 cart");
    CHECK(C.audio_mask & (1u << AUDIO_MMC5), "mmc5 audio enabled too");
    extern uint8_t expaudio_regs_vrc7[64];
    cart_cpu_write(&C, 0x9010, 0x30); cart_cpu_write(&C, 0x9030, 0xA5);
    CHECK(expaudio_regs_vrc7[0x30] == 0xA5, "vrc7 reg latched through router");
    cart_cpu_write(&C, 0x5100, 3); cart_cpu_write(&C, 0x5117, 0x85); CHECK(cart_cpu_read(&C, 0xE000) == 5, "mmc5 prg bank %u", cart_cpu_read(&C, 0xE000));
    cart_cpu_write(&C, 0x5205, 7); cart_cpu_write(&C, 0x5206, 9); CHECK(cart_cpu_read(&C, 0x5205) == 63, "mmc5 multiplier");
    cart_cpu_write(&C, 0x5105, 0x50); CHECK(C.nt_map[0] == NULL && C.nt_ciram_a10[0] == 0 && C.nt_ciram_a10[1] == 0 && C.nt_ciram_a10[2] == 1, "mmc5 nt map");
    cart_cpu_write(&C, 0x5106, 0x42); cart_cpu_write(&C, 0x5107, 2); cart_cpu_write(&C, 0x5105, 0xFF);
    CHECK(cart_ppu_read(&C, 0x2000) == 0x42 && cart_ppu_read(&C, 0x23C0) == 0xAA, "mmc5 fill mode");
    free(img);
}
static void test_vrc4_irq(void) {
    uint32_t len; uint8_t *img = make_ines(262144, 262144, 21, 1, true, &len);
    rom_info_t i; CHECK(cart_load(&C, img, len, NULL, &i) == LOAD_OK, "load vrc4a");
    cart_cpu_write(&C, 0x8000, 0x12); CHECK(cart_cpu_read(&C, 0x8000) == 0x12, "vrc4 prg0");
    cart_cpu_write(&C, 0xB000, 0x5); cart_cpu_write(&C, 0xB002, 0x1); CHECK(cart_ppu_read(&C, 0x0000) == (0x80 | 0x15), "vrc4a chr0 nibbles -> %02X", cart_ppu_read(&C, 0x0000));
    cart_cpu_write(&C, 0xF000, 0xE); cart_cpu_write(&C, 0xF002, 0xF); cart_cpu_write(&C, 0xF004, 0x06); /* latch FE, enable, cycle mode */
    for (int k = 0; k < 2; k++) cart_cpu_cycle(&C);
    CHECK(C.irq_line == 1, "vrc4 cycle irq after 2 cycles (cnt=%u)", C.s.vrc4.irq_counter);
    free(img);
}
static void test_all_mappers_init(void) {
    for (unsigned k = 0; k < mapper_count(); k++) {
        const mapper_desc_t *m = mapper_at(k);
        uint32_t len; uint8_t *img = make_ines(131072, 65536, m->id, 0, true, &len);
        rom_info_t i; load_result_t r = cart_load(&C, img, len, NULL, &i);
        CHECK(r == LOAD_OK, "mapper %u (%s) load: %s", m->id, m->name, cart_load_strerror(r));
        if (r == LOAD_OK) {
            for (unsigned a = 0x8000; a < 0x10000; a += 0x1000) (void)cart_cpu_read(&C, (uint16_t)a);
            for (unsigned a = 0; a < 0x3000; a += 0x400) (void)cart_ppu_read(&C, (uint16_t)a);
            for (unsigned a = 0x4020; a < 0x10000; a += 0x101) cart_cpu_write(&C, (uint16_t)a, (uint8_t)a);
            for (int n = 0; n < 2000; n++) cart_cpu_cycle(&C);
            for (unsigned s = 0; s < 8; s++) { CHECK(C.chr_map[s] != NULL, "mapper %u chr slot %u mapped", m->id, s); }
            for (unsigned s = 4; s < 8; s++) { CHECK(C.prg_map[s] != NULL, "mapper %u prg slot %u mapped", m->id, s); }
        }
        free(img);
    }
}
int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    test_crc(); test_header(); test_db(); test_mmc1(); test_mmc3(); test_mmc5_profile_vrc7(); test_vrc4_irq(); test_all_mappers_init();
    printf("%d checks, %d failures\n", checks, fails);
    return fails ? 1 : 0;
}
