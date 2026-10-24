/* famicart rev D, U1 firmware: PRG mapper / expansion-audio chip. */
#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "hardware/clocks.h"
#include "hardware/vreg.h"
#include "hardware/flash.h"
#include "hardware/sync.h"
#include "board.h"
#include "bus_revd.h"
#include "bankout.h"
#include "maplink.h"
#include "norflash.h"
#include "library.h"
#include "../core/cartload.h"
#include "../core/mapper.h"
#include "../core/rom.h"
#include "../core/audio/expaudio.h"
#include <stdio.h>
#include <string.h>

void audio_out_init(void); void audio_out_pump(void);
void usb_cmd_init(void); void usb_cmd_poll(void);

cart_t g_cart; rom_info_t g_info; lib_header_t g_lib; lib_entry_t g_entry; load_result_t g_load = LOAD_ERR_INSPECT; bool g_running;

const lib_header_t *lib_hdr_flash(void) { return (const lib_header_t *)(XIP_BASE + FC_FLASH_ROM_SLOT); }
const lib_entry_t *lib_entry_flash(unsigned i) { return (const lib_entry_t *)(XIP_BASE + FC_FLASH_ROM_SLOT + LIB_ENTRY_SIZE * (1 + i)); }

/* Send rom_info + profile + flash bases to U2 so it builds the same cart. */
static void send_load_to_u2(const lib_entry_t *e, const rom_info_t *info) {
    struct { rom_info_t info; cart_profile_t prof; uint32_t chr_base_bank; uint8_t has_prof; uint8_t pad[3]; } blob;
    memset(&blob, 0, sizeof blob);
    blob.info = *info; blob.prof = e->profile; blob.has_prof = (e->flags & 1) ? 1 : 0; blob.chr_base_bank = e->chr_off >> 10;
    const uint8_t *p = (const uint8_t *)&blob; uint32_t n = sizeof blob;
    maplink_send(link_frame(LINK_T_LOAD_BEGIN, n));
    for (uint32_t i = 0; i < n; i += 3) { uint32_t v = p[i] | (i + 1 < n ? p[i + 1] << 8 : 0) | (i + 2 < n ? p[i + 2] << 16 : 0); maplink_send(link_frame(LINK_T_LOAD_DATA, v)); }
    maplink_send(link_frame(LINK_T_LOAD_END, 0));
    if (!maplink_wait_ack(LINK_R_LOADED, 500000)) printf("WARN: U2 did not confirm the load\n");
}

bool boot_entry(unsigned slot) {
    const lib_entry_t *e = lib_entry_flash(slot);
    if (e->magic != LIB_MAGIC) return false;
    g_entry = *e;
    if (!rom_inspect_header(e->header, e->prg_size + e->chr_size, e->data_crc, &g_info)) return false;
    g_load = cart_load_from_info(&g_cart, NULL, &g_info, (e->flags & 1) ? &e->profile : NULL);
    if (g_load != LOAD_OK) return false;
    bankout_set_cart(&g_cart, e->prg_off >> 13);
    send_load_to_u2(e, &g_info);
    return true;
}

int main(void) {
    set_sys_clock_khz(FC_SYS_CLOCK_KHZ, true);
    /* safe defaults before anything else: console isolated? NO -- the pull-ups already map the boot bank; keep buffers on */
    gpio_init(PIN_ISOLATE); gpio_set_dir(PIN_ISOLATE, true); gpio_put(PIN_ISOLATE, 0);
    gpio_init(PIN_PRG_NWE); gpio_set_dir(PIN_PRG_NWE, true); gpio_put(PIN_PRG_NWE, 1);
    bankout_init();
    stdio_init_all();
    maplink_init();
    maplink_send(link_frame(LINK_T_SYNC, 0));
    maplink_send(link_frame(LINK_T_CMD, (LINK_C_RESET << 16)));

    const lib_header_t *h = lib_hdr_flash();
    if (h->magic == LIB_MAGIC) { g_lib = *h; if (boot_entry(g_lib.current)) g_running = true; }
    else memset(&g_lib, 0, sizeof g_lib);

    busd_init(&g_cart);                  /* snoop + boot-flag service start here (bank lines still = boot bank) */
    audio_out_init();
    if (g_running) { busd_boot_flags(1, 1); maplink_send(link_frame(LINK_T_CMD, (LINK_C_BOOT << 16) | 1)); }   /* stub: go */
    usb_cmd_init();
    absolute_time_t next = make_timeout_time_ms(2000);
    for (;;) {
        if (g_running) audio_out_pump();
        usb_cmd_poll();
        if (time_reached(next)) { next = make_timeout_time_ms(10000); extern void usb_cmd_print_info(void); usb_cmd_print_info(); }
    }
}
