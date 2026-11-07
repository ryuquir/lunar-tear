/* rev E, U1 USB-CDC commands: ROM library in U1's own 4 MB flash.
 *   INFO | RESET | BOOTSEL | LIB | LIBSEL n | LIBDEL n | LIBCLR | LIBADD <prg_bytes> <chr_bytes> <name>
 * LIBADD: the host sends the 16-byte iNES header, then PRG, then CHR. The cart may stay in the console: the CPU is
 * parked in JMP $4C4C (served from SRAM) while the flash is written, and the new game starts when it is done. */
#include "pico/stdlib.h"
#include "pico/bootrom.h"
#include "hardware/watchdog.h"
#include "hardware/flash.h"
#include "hardware/sync.h"
#include "hardware/clocks.h"
#include "board.h"
#include "reve_cpu.h"
#include "../core/cartload.h"
#include "../core/mapper.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

static char line[160]; static unsigned line_len;
static uint8_t sector[FLASH_SECTOR_SIZE] __attribute__((aligned(4)));
static lib_header_t lib;

void usb_cmd_init(void) { line_len = 0; const lib_header_t *h = lib_hdr_flash(); if (h->magic == LIB_MAGIC) lib = *h; else { memset(&lib, 0, sizeof lib); lib.magic = LIB_MAGIC; } }
static void reboot(void) { printf("OK rebooting\n"); sleep_ms(50); watchdog_reboot(0, 0, 10); for (;;) tight_loop_contents(); }

static void flash_write_sector(uint32_t off, const uint8_t *data) {
    uint32_t ints = save_and_disable_interrupts();
    flash_range_erase(off, FLASH_SECTOR_SIZE);
    flash_range_program(off, data, FLASH_SECTOR_SIZE);
    restore_interrupts(ints);
}
/* index: header (256 B) + 63 entries x 256 B = 16 KB = 4 sectors at FC_FLASH_LIB */
static void lib_store(unsigned idx, const lib_entry_t *e) {
    unsigned s = (LIB_ENTRY_SIZE * (1 + idx)) / FLASH_SECTOR_SIZE;
    memcpy(sector, (const void *)(XIP_BASE + FC_FLASH_LIB + s * FLASH_SECTOR_SIZE), FLASH_SECTOR_SIZE);
    if (e) memcpy(sector + (LIB_ENTRY_SIZE * (1 + idx)) % FLASH_SECTOR_SIZE, e, sizeof *e);
    if (s == 0) memcpy(sector, &lib, sizeof lib);
    flash_write_sector(FC_FLASH_LIB + s * FLASH_SECTOR_SIZE, sector);
    if (s != 0) { memcpy(sector, (const void *)(XIP_BASE + FC_FLASH_LIB), FLASH_SECTOR_SIZE); memcpy(sector, &lib, sizeof lib); flash_write_sector(FC_FLASH_LIB, sector); }
}
static uint32_t lib_free_offset(void) {
    uint32_t end = 0;
    for (unsigned i = 0; i < LIB_MAX - 1; i++) { const lib_entry_t *e = lib_entry_flash(i); if (e->magic == LIB_MAGIC && e->prg_off + e->prg_size + e->chr_size > end) end = e->prg_off + e->prg_size + e->chr_size; }
    return (end + FLASH_SECTOR_SIZE - 1) & ~(uint32_t)(FLASH_SECTOR_SIZE - 1);
}
static bool rx_block(uint8_t *dst, uint32_t n) { for (uint32_t i = 0; i < n; i++) { int c = getchar_timeout_us(3000000); if (c < 0) return false; dst[i] = (uint8_t)c; } return true; }

static void cmd_libadd(uint32_t prg, uint32_t chr, const char *name) {
    uint32_t off = lib_free_offset(), total = prg + chr;
    if (prg < 8192 || (prg & 0x1FFF) || (chr & 0x1FFF)) { printf("ERR size\n"); return; }
    if (FC_FLASH_DATA + off + total > FC_FLASH_END) { printf("ERR flash full (%lu KB free) - LIBDEL or LIBCLR first\n", (unsigned long)(FC_FLASH_END - FC_FLASH_DATA - off) / 1024); return; }
    unsigned idx = 0; while (idx < LIB_MAX - 1 && lib_entry_flash(idx)->magic == LIB_MAGIC) idx++;
    if (idx >= LIB_MAX - 1) { printf("ERR library full\n"); return; }
    lib_entry_t e; memset(&e, 0xFF, sizeof e); memset(e.name, 0, sizeof e.name); strncpy(e.name, name, sizeof e.name - 1);
    e.magic = LIB_MAGIC; e.flags = 0; e.prg_off = off; e.prg_size = prg; e.chr_off = off + prg; e.chr_size = chr;
    printf("READY %lu %lu slot %u at %lX\n", (unsigned long)prg, (unsigned long)chr, idx, (unsigned long)off);
    if (!rx_block(e.header, 16)) { printf("ERR header timeout\n"); return; }
    reve_flash_begin();
    uint32_t crc = 0; bool ok = true;
    for (uint32_t p = 0; p < total && ok; p += FLASH_SECTOR_SIZE) {
        uint32_t n = total - p < FLASH_SECTOR_SIZE ? total - p : FLASH_SECTOR_SIZE;
        memset(sector, 0xFF, sizeof sector);
        if (!rx_block(sector, n)) { ok = false; break; }
        crc = fc_crc32(crc, sector, n);
        flash_write_sector(FC_FLASH_DATA + off + p, sector);
        if ((p & 0xFFFF) == 0) printf(".");
    }
    reve_flash_end();
    if (!ok) { printf("\nERR receive timeout\n"); return; }
    uint32_t vcrc = fc_crc32(0, (const uint8_t *)(XIP_BASE + FC_FLASH_DATA + off), total);
    e.data_crc = crc;
    lib.magic = LIB_MAGIC; lib.current = idx; lib.prg_used = off + total;
    reve_flash_begin(); lib_store(idx, &e); reve_flash_end();
    rom_info_t info; bool insp = rom_inspect_header(e.header, total, crc, &info);
    printf("\nOK slot %u crc %08lX verify %s mapper %u%s (%s)\n", idx, (unsigned long)crc, vcrc == crc ? "ok" : "FAILED", insp ? info.mapper : 0,
           insp && !mapper_find(info.mapper) ? " NOT SUPPORTED YET" : "", insp ? info.note : "no header");
    if (vcrc == crc) reve_boot(idx);
}
void usb_cmd_print_info(void) {
    printf("\n[famicart rev E / U1 CPU] sysclk=%lu kHz  lib: current=%lu  free=%lu KB\n", clock_get_hz(clk_sys) / 1000, (unsigned long)lib.current,
           (unsigned long)(FC_FLASH_END - FC_FLASH_DATA - lib_free_offset()) / 1024);
    if (g_running) printf("  game : %s mapper=%u sub=%u prg=%luK chr=%luK %s\n", g_entry.name, g_info.mapper, g_info.submapper, (unsigned long)g_info.prg_size / 1024, (unsigned long)g_info.chr_size / 1024, g_info.note);
    else printf("  no game running (CPU parked at $4C4C)\n");
    printf("  bus  : reads=%lu writes=%lu  link polls=%lu missed=%lu  drops: events=%lu link=%lu\n", (unsigned long)st_reads, (unsigned long)st_writes,
           (unsigned long)st_polls, (unsigned long)st_poll_miss, (unsigned long)st_evq_drop, (unsigned long)st_link_drop);
    printf("  cmds : INFO | RESET | BOOTSEL | LIB | LIBSEL n | LIBDEL n | LIBCLR | LIBADD <prg> <chr> <name>\n");
}
static void handle(char *l) {
    if (!strcmp(l, "INFO")) usb_cmd_print_info();
    else if (!strcmp(l, "RESET")) reboot();
    else if (!strcmp(l, "BOOTSEL")) { printf("OK bootsel\n"); sleep_ms(50); reset_usb_boot(0, 0); }
    else if (!strcmp(l, "LIB")) { for (unsigned i = 0; i < LIB_MAX - 1; i++) { const lib_entry_t *e = lib_entry_flash(i); if (e->magic == LIB_MAGIC) printf("%2u%c %-32s prg %5luK chr %5luK crc %08lX\n", i, i == lib.current ? '*' : ' ', e->name, (unsigned long)e->prg_size / 1024, (unsigned long)e->chr_size / 1024, (unsigned long)e->data_crc); } printf("OK\n"); }
    else if (!strncmp(l, "LIBSEL ", 7)) { unsigned n = strtoul(l + 7, NULL, 10); if (n >= LIB_MAX - 1 || lib_entry_flash(n)->magic != LIB_MAGIC) { printf("ERR empty slot\n"); return; }
        lib.current = n; reve_flash_begin(); lib_store(0, NULL); reve_flash_end(); printf(reve_boot(n) ? "OK\n" : "ERR boot failed\n"); }
    else if (!strncmp(l, "LIBDEL ", 7)) { unsigned n = strtoul(l + 7, NULL, 10); if (n >= LIB_MAX - 1) { printf("ERR slot\n"); return; } lib_entry_t e; memset(&e, 0xFF, sizeof e); reve_flash_begin(); lib_store(n, &e); reve_flash_end(); printf("OK\n"); }
    else if (!strcmp(l, "LIBCLR")) { reve_flash_begin(); memset(sector, 0xFF, sizeof sector); for (unsigned s = 0; s < 4; s++) flash_write_sector(FC_FLASH_LIB + s * FLASH_SECTOR_SIZE, sector);
        memset(&lib, 0, sizeof lib); lib.magic = LIB_MAGIC; lib_store(0, NULL); reve_flash_end(); printf("OK library cleared\n"); }
    else if (!strncmp(l, "LIBADD ", 7)) { char *end; uint32_t prg = strtoul(l + 7, &end, 10); uint32_t chr = strtoul(end, &end, 10); while (*end == ' ') end++; cmd_libadd(prg, chr, *end ? end : "untitled"); }
    else if (*l) printf("ERR unknown command\n");
}
void usb_cmd_poll(void) {
    for (;;) { int c = getchar_timeout_us(0); if (c < 0) return;
        if (c == '\r' || c == '\n') { line[line_len] = 0; line_len = 0; handle(line); } else if (line_len < sizeof line - 1) line[line_len++] = (char)c; }
}
