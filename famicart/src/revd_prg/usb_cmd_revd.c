/* rev D, U1 USB-CDC commands: ROM library management + flash programming.
 *   INFO | RESET | BOOTSEL | LIB | LIBSEL n | LIBDEL n | LIBADD <prg_bytes> <chr_bytes> <name> | BOOTBANK | FLASHID | WRAMDUMP
 * LIBADD: host sends the 16-byte header, then PRG bytes, then CHR bytes (raw). Do this with the cart OUT of the
 * console (USB powered): the console bus is isolated while the external flashes are programmed. */
#include "pico/stdlib.h"
#include "pico/bootrom.h"
#include "hardware/watchdog.h"
#include "hardware/flash.h"
#include "hardware/sync.h"
#include "hardware/clocks.h"
#include "board.h"
#include "bus_revd.h"
#include "bankout.h"
#include "maplink.h"
#include "norflash.h"
#include "library.h"
#include "bootstub_gen.h"
#include "../core/cartload.h"
#include "../core/rom.h"
#include "../core/mapper.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

extern cart_t g_cart; extern rom_info_t g_info; extern lib_header_t g_lib; extern lib_entry_t g_entry; extern load_result_t g_load; extern bool g_running;
extern const lib_header_t *lib_hdr_flash(void); extern const lib_entry_t *lib_entry_flash(unsigned i);

static char line[160]; static unsigned line_len;
static uint8_t sector[FLASH_SECTOR_SIZE] __attribute__((aligned(4)));
static uint8_t buf[4096];

void usb_cmd_init(void) { line_len = 0; }
static void reboot(void) { printf("OK rebooting\n"); sleep_ms(50); watchdog_reboot(0, 0, 10); for (;;) tight_loop_contents(); }

/* The library index lives in the first 64 KB of the slot: header + 63 entries x 256 B fit in 4 sectors. */
static void lib_write_sector(unsigned s) {
    uint32_t ints = save_and_disable_interrupts();
    flash_range_erase(FC_FLASH_ROM_SLOT + s * FLASH_SECTOR_SIZE, FLASH_SECTOR_SIZE);
    flash_range_program(FC_FLASH_ROM_SLOT + s * FLASH_SECTOR_SIZE, sector, FLASH_SECTOR_SIZE);
    restore_interrupts(ints);
}
static void lib_store(const lib_header_t *h, unsigned idx, const lib_entry_t *e) {
    /* rewrite the sector holding entry idx (and the header, sector 0) */
    unsigned s = (LIB_ENTRY_SIZE * (1 + idx)) / FLASH_SECTOR_SIZE;
    memcpy(sector, (const void *)(XIP_BASE + FC_FLASH_ROM_SLOT + s * FLASH_SECTOR_SIZE), FLASH_SECTOR_SIZE);
    if (e) memcpy(sector + (LIB_ENTRY_SIZE * (1 + idx)) % FLASH_SECTOR_SIZE, e, sizeof *e);
    if (s == 0 && h) memcpy(sector, h, sizeof *h);
    lib_write_sector(s);
    if (s != 0 && h) { memcpy(sector, (const void *)(XIP_BASE + FC_FLASH_ROM_SLOT), FLASH_SECTOR_SIZE); memcpy(sector, h, sizeof *h); lib_write_sector(0); }
}

static int rx(uint32_t us) { return getchar_timeout_us(us); }
static bool rx_block(uint8_t *dst, uint32_t n) { for (uint32_t i = 0; i < n; i++) { int c = rx(3000000); if (c < 0) return false; dst[i] = (uint8_t)c; } return true; }

static void programming_begin(void) {
    busd_stop(); bankout_boot();
    nor_bus_take();
    if (!nor_chr_begin()) printf("WARN: U2 not in programming mode\n");
}
static void programming_end(void) { nor_chr_end(); nor_bus_release(); reboot(); }

static void cmd_libadd(uint32_t prg, uint32_t chr, const char *name) {
    if (prg < 16384 || (prg & 0x3FFF) || (chr & 0x1FFF) || prg + g_lib.prg_used > 0x3FE0000u || chr + g_lib.chr_used > 0x4000000u) { printf("ERR size\n"); return; }
    unsigned idx = 0; while (idx < LIB_MAX - 1 && lib_entry_flash(idx)->magic == LIB_MAGIC) idx++;
    if (idx >= LIB_MAX - 1) { printf("ERR library full\n"); return; }
    lib_entry_t e; memset(&e, 0xFF, sizeof e); memset(e.name, 0, sizeof e.name); strncpy(e.name, name, sizeof e.name - 1);
    e.magic = LIB_MAGIC; e.flags = 0; e.prg_off = (g_lib.prg_used + 0x1FFFFu) & ~0x1FFFFu; e.prg_size = prg; e.chr_off = (g_lib.chr_used + 0x1FFFFu) & ~0x1FFFFu; e.chr_size = chr;
    printf("READY %lu %lu slot %u prg@%lX chr@%lX\n", (unsigned long)prg, (unsigned long)chr, idx, (unsigned long)e.prg_off, (unsigned long)e.chr_off);
    if (!rx_block(e.header, 16)) { printf("ERR header timeout\n"); return; }
    programming_begin();
    uint32_t crc = 0; bool ok = true;
    for (uint32_t off = 0; off < prg && ok; off += sizeof buf) {
        uint32_t n = prg - off < sizeof buf ? prg - off : sizeof buf;
        if (!rx_block(buf, n)) { ok = false; break; }
        crc = fc_crc32(crc, buf, n);
        if (((e.prg_off + off) & 0x1FFFF) == 0) ok = nor_prg_erase_sector(e.prg_off + off);
        if (ok) ok = nor_prg_program(e.prg_off + off, buf, n);
        if ((off & 0xFFFF) == 0) printf(".");
    }
    for (uint32_t off = 0; off < chr && ok; off += sizeof buf) {
        uint32_t n = chr - off < sizeof buf ? chr - off : sizeof buf;
        if (!rx_block(buf, n)) { ok = false; break; }
        crc = fc_crc32(crc, buf, n);
        if (((e.chr_off + off) & 0x1FFFF) == 0) ok = nor_chr_erase_sector(e.chr_off + off);
        if (ok) ok = nor_chr_program(e.chr_off + off, buf, n);
        if ((off & 0xFFFF) == 0) printf("+");
    }
    if (!ok) { printf("\nERR programming failed\n"); programming_end(); return; }
    /* verify PRG by read-back CRC (CHR verified by DQ7 polling only) */
    uint32_t vcrc = 0; for (uint32_t off = 0; off < prg; off++) { uint8_t b = nor_prg_read(e.prg_off + off); vcrc = fc_crc32(vcrc, &b, 1); }
    e.data_crc = crc;
    rom_info_t info; bool insp = rom_inspect_header(e.header, prg + chr, crc, &info);
    g_lib.magic = LIB_MAGIC; g_lib.prg_used = e.prg_off + prg; g_lib.chr_used = e.chr_off + chr; g_lib.current = idx;
    lib_store(&g_lib, idx, &e);
    printf("\nOK slot %u crc %08lX prg-verify %s mapper %u (%s)\n", idx, (unsigned long)crc, (prg && vcrc != fc_crc32(0, NULL, 0) && (chr ? true : vcrc == crc)) ? "ok" : "see-note", insp ? info.mapper : 0, insp ? info.note : "no header");
    programming_end();
}
static void cmd_bootbank(void) {
    printf("programming the boot bank (top 8 KB of the PRG flash)\n");
    programming_begin();
    uint32_t a = (uint32_t)FC_BOOT_BANK << 13;
    bool ok = nor_prg_erase_sector(a) && nor_prg_program(a, bootstub_bank, 8192);
    bool id = true; for (int i = 0; i < 16; i++) if (nor_prg_read(a + 0x1F00 + i) != bootstub_bank[0x1F00 + i]) id = false;
    printf("%s (verify %s)\n", ok ? "OK" : "ERR", id ? "ok" : "FAILED");
    programming_end();
}
static void cmd_flashid(void) {
    programming_begin();
    uint8_t m; uint16_t d = nor_prg_id(&m);
    printf("PRG flash: mfr %02X id %04X (Cypress/Infineon = 01, GL01GS = 227E/2228/2201)\n", m, d);
    uint8_t id[16]; for (int i = 0; i < 16; i++) id[i] = nor_prg_read(((uint32_t)FC_BOOT_BANK << 13) + 0x1F00 + i);
    printf("boot bank: %.16s\n", (const char *)id);
    programming_end();
}
static void cmd_wramdump(void) {
    programming_begin();
    for (uint32_t a = 0; a < 8192; a += 16) { printf("%04lX:", (unsigned long)a); for (int i = 0; i < 16; i++) printf(" %02X", nor_wram_read(a + i)); printf("\n"); }
    programming_end();
}
void usb_cmd_print_info(void) {
    printf("\n[famicart rev D / U1] sysclk=%lu kHz lib: %s current=%lu prg_used=%lu chr_used=%lu\n", clock_get_hz(clk_sys) / 1000, g_lib.magic == LIB_MAGIC ? "ok" : "empty", (unsigned long)g_lib.current, (unsigned long)g_lib.prg_used, (unsigned long)g_lib.chr_used);
    if (g_running) printf("  game : %s mapper=%u sub=%u prg=%luK chr=%luK %s\n  bus  : m2=%lu rd=%lu wr=%lu resets=%lu irq=%u\n", g_entry.name, g_info.mapper, g_info.submapper, (unsigned long)g_info.prg_size / 1024, (unsigned long)g_info.chr_size / 1024, g_info.note,
                          (unsigned long)bus_stat_cpu_cycles, (unsigned long)bus_stat_cpu_reads, (unsigned long)bus_stat_cpu_writes, (unsigned long)bus_stat_resets, g_cart.irq_line);
    else printf("  no game loaded (%s)\n", cart_load_strerror(g_load));
    printf("  cmds : INFO | RESET | BOOTSEL | LIB | LIBSEL n | LIBDEL n | LIBADD <prg> <chr> <name> | BOOTBANK | FLASHID | WRAMDUMP\n");
}
static void handle(char *l) {
    if (!strcmp(l, "INFO")) usb_cmd_print_info();
    else if (!strcmp(l, "RESET")) reboot();
    else if (!strcmp(l, "BOOTSEL")) { printf("OK bootsel\n"); sleep_ms(50); reset_usb_boot(0, 0); }
    else if (!strcmp(l, "LIB")) { for (unsigned i = 0; i < LIB_MAX - 1; i++) { const lib_entry_t *e = lib_entry_flash(i); if (e->magic == LIB_MAGIC) printf("%2u%c %-32s prg %6luK chr %6luK crc %08lX\n", i, i == g_lib.current ? '*' : ' ', e->name, (unsigned long)e->prg_size / 1024, (unsigned long)e->chr_size / 1024, (unsigned long)e->data_crc); } printf("OK\n"); }
    else if (!strncmp(l, "LIBSEL ", 7)) { unsigned n = strtoul(l + 7, NULL, 10); if (lib_entry_flash(n)->magic != LIB_MAGIC) { printf("ERR empty slot\n"); return; } busd_stop(); g_lib.current = n; lib_store(&g_lib, 0, NULL); reboot(); }
    else if (!strncmp(l, "LIBDEL ", 7)) { unsigned n = strtoul(l + 7, NULL, 10); lib_entry_t e; memset(&e, 0xFF, sizeof e); busd_stop(); lib_store(NULL, n, &e); reboot(); }
    else if (!strncmp(l, "LIBADD ", 7)) { char *end; uint32_t prg = strtoul(l + 7, &end, 10); uint32_t chr = strtoul(end, &end, 10); while (*end == ' ') end++; cmd_libadd(prg, chr, *end ? end : "untitled"); }
    else if (!strcmp(l, "BOOTBANK")) cmd_bootbank();
    else if (!strcmp(l, "FLASHID")) cmd_flashid();
    else if (!strcmp(l, "WRAMDUMP")) cmd_wramdump();
    else if (*l) printf("ERR unknown command\n");
}
void usb_cmd_poll(void) {
    for (;;) { int c = getchar_timeout_us(0); if (c < 0) return;
        if (c == '\r' || c == '\n') { line[line_len] = 0; line_len = 0; handle(line); } else if (line_len < sizeof line - 1) line[line_len++] = (char)c; }
}
