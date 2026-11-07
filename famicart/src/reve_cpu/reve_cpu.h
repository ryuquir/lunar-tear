#pragma once
#include "../pico/library.h"
#include "../core/cart.h"
#include "../core/rom.h"
#ifndef FC_PRG_POOL
#define FC_PRG_POOL (384 * 1024)
#endif
extern cart_t g_cart; extern rom_info_t g_info; extern bool g_running; extern lib_entry_t g_entry;
extern volatile uint32_t st_reads, st_writes, st_evq_drop, st_link_drop, st_polls, st_poll_miss;
const lib_header_t *lib_hdr_flash(void);
const lib_entry_t *lib_entry_flash(unsigned i);
bool reve_boot(unsigned slot);
void reve_park(void);
void reve_flash_begin(void);
void reve_flash_end(void);
void reve_link_cmd(uint8_t sub, uint8_t arg);
int  reve_link_poll(uint8_t node, uint32_t timeout_us);
void usb_cmd_init(void);
void usb_cmd_poll(void);
void usb_cmd_print_info(void);
