/* Host test of the rev D "virtual ROM" core mode: table pointers must translate to bank numbers. Built with -DFC_VIRTUAL_ROM=1. */
#include "cart.h"
#include "cartload.h"
#include "mapper.h"
#include "rom.h"
#include <stdio.h>
#include <string.h>
static int checks, fails;
#define CHECK(c, ...) do { checks++; if (!(c)) { fails++; printf("FAIL %s:%d: ", __FILE__, __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)
static uint32_t prg_bank(const cart_t *c, int win) { const uint8_t *p = c->prg_map[win]; return (uint32_t)(((uintptr_t)p - FC_VROM_PRG) >> 13); }
static int is_wram(const cart_t *c, int win) { const uint8_t *p = c->prg_map[win]; return p && (uintptr_t)p >= FC_VROM_WRAM && (uintptr_t)p < FC_VROM_WRAM + FC_VROM_WRAM_SIZE; }
static uint32_t chr_bank(const cart_t *c, int slot) { return (uint32_t)(((uintptr_t)c->chr_map[slot] - FC_VROM_CHR) >> 10); }
int main(void) {
    uint8_t hdr[16] = { 'N', 'E', 'S', 0x1A, 8, 16, 0x40 | 0x02, 0, 0, 0, 0, 0, 0, 0, 0, 0 };   /* 128K PRG, 128K CHR, mapper 4, battery */
    rom_info_t info; cart_t c;
    CHECK(rom_inspect_header(hdr, 262144, 0x12345678, &info), "inspect header");
    CHECK(info.mapper == 4 && info.prg_size == 131072 && info.chr_size == 131072, "sizes %u %lu %lu", info.mapper, (unsigned long)info.prg_size, (unsigned long)info.chr_size);
    CHECK(cart_load_from_info(&c, NULL, &info, NULL) == LOAD_OK, "load virtual");
    CHECK(c.prg_rom == (const uint8_t *)FC_VROM_PRG && c.chr == (uint8_t *)FC_VROM_CHR, "virtual bases");
    CHECK(prg_bank(&c, 7) == 15, "MMC3 $E000 = last bank (%lu)", (unsigned long)prg_bank(&c, 7));
    c.tables_dirty = 0;
    cart_cpu_write(&c, 0x8000, 6); cart_cpu_write(&c, 0x8001, 5);        /* R6 = 5 -> $8000 */
    CHECK(c.tables_dirty, "dirty after bank write");
    CHECK(prg_bank(&c, 4) == 5, "MMC3 $8000 bank 5 (%lu)", (unsigned long)prg_bank(&c, 4));
    cart_cpu_write(&c, 0x8000, 2); cart_cpu_write(&c, 0x8001, 9);        /* R2 = 9 -> 1K slot 4 */
    CHECK(chr_bank(&c, 4) == 9, "MMC3 chr slot4 = 9 (%lu)", (unsigned long)chr_bank(&c, 4));
    cart_cpu_write(&c, 0xA001, 0x80);                                      /* WRAM enable */
    CHECK(is_wram(&c, 3), "WRAM mapped at $6000");
    cart_cpu_write(&c, 0x6000, 0x55);                                      /* must not deref the virtual pointer */
    CHECK(c.open_bus == 0x55, "write went through safely");
    /* CHR-RAM game: UNROM */
    uint8_t hdr2[16] = { 'N', 'E', 'S', 0x1A, 8, 0, 0x20, 0, 0, 0, 0, 0, 0, 0, 0, 0 };
    CHECK(rom_inspect_header(hdr2, 131072, 1, &info), "inspect UNROM");
    CHECK(cart_load_from_info(&c, NULL, &info, NULL) == LOAD_OK, "load UNROM");
    CHECK(c.chr == (uint8_t *)FC_VROM_CHRRAM && c.chr_is_ram, "CHR-RAM virtual");
    cart_cpu_write(&c, 0x8000, 3);
    CHECK(prg_bank(&c, 4) == 6 && prg_bank(&c, 5) == 7 && prg_bank(&c, 7) == 15, "UNROM banks %lu %lu %lu", (unsigned long)prg_bank(&c, 4), (unsigned long)prg_bank(&c, 5), (unsigned long)prg_bank(&c, 7));
    /* four-screen: nametables in CHR RAM top */
    uint8_t hdr3[16] = { 'N', 'E', 'S', 0x1A, 8, 16, 0x08 | 0x40, 0, 0, 0, 0, 0, 0, 0, 0, 0 };
    CHECK(rom_inspect_header(hdr3, 262144, 2, &info) && cart_load_from_info(&c, NULL, &info, NULL) == LOAD_OK, "4-screen load");
    CHECK(c.nt_map[2] == (uint8_t *)(FC_VROM_CHRRAM + FC_VROM_CHRRAM_SIZE - 2048), "NT2 in CHR RAM top");
    printf("%d checks, %d failures\n", checks, fails);
    return fails ? 1 : 0;
}
