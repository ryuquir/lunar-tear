#include "usb_cmd.h"
#include "board.h"
#include "bus.h"
#include "romslot.h"
#include "../core/rom.h"
#include "../core/profile.h"
#include "pico/stdlib.h"
#include "pico/bootrom.h"
#include "hardware/watchdog.h"
#include "hardware/flash.h"
#include "hardware/sync.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#define ROMSLOT_HDR 256u
static char line[96]; static unsigned line_len;
static uint8_t page[FLASH_SECTOR_SIZE] __attribute__((aligned(4)));

void usb_cmd_init(void) { line_len = 0; }

static void reboot(void) { printf("OK rebooting\n"); sleep_ms(50); watchdog_reboot(0, 0, 10); for (;;) tight_loop_contents(); }

/* Erase/program the ROM slot while the bus front-end is stopped (XIP is unavailable during flash ops). */
static bool flash_write_slot(uint32_t offset_in_slot, const uint8_t *src, uint32_t len) {
    uint32_t base = FC_FLASH_ROM_SLOT + offset_in_slot;
    if (base % FLASH_SECTOR_SIZE || base + len > FC_FLASH_ROM_SLOT + FC_FLASH_ROM_SLOT_MAX) return false;
    uint32_t ints = save_and_disable_interrupts();
    flash_range_erase(base, (len + FLASH_SECTOR_SIZE - 1) & ~(FLASH_SECTOR_SIZE - 1));
    flash_range_program(base, src, (len + FLASH_PAGE_SIZE - 1) & ~(FLASH_PAGE_SIZE - 1));
    restore_interrupts(ints);
    return true;
}

static int read_byte_timeout(uint32_t us) { return getchar_timeout_us(us); }

static void cmd_load(uint32_t nbytes, uint32_t crc_expect) {
    if (nbytes < 16 || nbytes > FC_FLASH_ROM_SLOT_MAX - ROMSLOT_HDR) { printf("ERR size\n"); return; }
    printf("READY %lu\n", (unsigned long)nbytes);
    bus_stop();                                   /* the console sees an open bus from here on; reset it afterwards */
    /* keep the existing profile header (sector 0 of the slot) unless it is invalid */
    const uint8_t *slot = (const uint8_t *)(XIP_BASE + FC_FLASH_ROM_SLOT);
    memcpy(page, slot, ROMSLOT_HDR);
    if (!profile_validate((const cart_profile_t *)page)) { cart_profile_t pf; profile_default(&pf); memset(page, 0xFF, ROMSLOT_HDR); memcpy(page, &pf, sizeof pf); }
    uint32_t received = 0, fill = ROMSLOT_HDR, flash_off = 0;
    while (received < nbytes) {
        int c = read_byte_timeout(2000000);
        if (c < 0) { printf("ERR timeout at %lu\n", (unsigned long)received); reboot(); }
        page[fill++] = (uint8_t)c; received++;
        if (fill == FLASH_SECTOR_SIZE || received == nbytes) {
            if (received == nbytes) memset(page + fill, 0xFF, FLASH_SECTOR_SIZE - fill);
            if (!flash_write_slot(flash_off, page, FLASH_SECTOR_SIZE)) { printf("ERR flash\n"); reboot(); }
            flash_off += FLASH_SECTOR_SIZE; fill = 0;
            if ((flash_off & 0xFFFF) == 0) printf(".");
        }
    }
    /* verify */
    uint32_t vcrc = fc_crc32(0, slot + ROMSLOT_HDR, nbytes);
    if (crc_expect && vcrc != crc_expect) printf("ERR crc %08lX != %08lX\n", (unsigned long)vcrc, (unsigned long)crc_expect);
    else printf("OK %lu bytes crc %08lX\n", (unsigned long)nbytes, (unsigned long)vcrc);
    reboot();
}

static void cmd_profile(const char *hex) {
    cart_profile_t pf; uint8_t *b = (uint8_t *)&pf;
    if (strlen(hex) < 2 * sizeof pf) { printf("ERR need %u hex bytes\n", (unsigned)sizeof pf); return; }
    for (unsigned i = 0; i < sizeof pf; i++) { char t[3] = { hex[2 * i], hex[2 * i + 1], 0 }; b[i] = (uint8_t)strtoul(t, NULL, 16); }
    if (!profile_validate(&pf)) { printf("ERR profile crc\n"); return; }
    bus_stop();
    const uint8_t *slot = (const uint8_t *)(XIP_BASE + FC_FLASH_ROM_SLOT);
    memcpy(page, slot, FLASH_SECTOR_SIZE);            /* first sector holds header + start of image */
    memset(page, 0xFF, ROMSLOT_HDR); memcpy(page, &pf, sizeof pf);
    if (!flash_write_slot(0, page, FLASH_SECTOR_SIZE)) { printf("ERR flash\n"); reboot(); }
    reboot();
}


static void handle(char *l) {
    if (!strcmp(l, "INFO")) usb_cmd_print_info();
    else if (!strcmp(l, "RESET")) reboot();
    else if (!strcmp(l, "BOOTSEL")) { printf("OK bootsel\n"); sleep_ms(50); reset_usb_boot(0, 0); }
    else if (!strncmp(l, "LOAD ", 5)) { char *end; uint32_t n = strtoul(l + 5, &end, 10); uint32_t crc = (*end) ? strtoul(end, NULL, 16) : 0; cmd_load(n, crc); }
    else if (!strncmp(l, "PROFILE ", 8)) cmd_profile(l + 8);
    else if (*l) printf("ERR unknown command\n");
}

void usb_cmd_poll(void) {
    for (;;) {
        int c = getchar_timeout_us(0);
        if (c < 0) return;
        if (c == '\r' || c == '\n') { line[line_len] = 0; line_len = 0; handle(line); }
        else if (line_len < sizeof line - 1) line[line_len++] = (char)c;
    }
}
