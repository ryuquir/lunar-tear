#include "norflash.h"
#include "bankout.h"
#include "maplink.h"
#include "board.h"
#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include "hardware/structs/sio.h"
#include <string.h>

#define ADDR_MASK 0x7FFFu          /* CA0-14 */
#define DATA_SHIFT PIN_CPU_DATA_BASE
#define DATA_MASK (0xFFu << DATA_SHIFT)
static inline void dly(unsigned n) { while (n--) __asm volatile("nop"); }   /* ~7 ns per iteration @150 MHz */

static void set_addr(uint32_t a26) {
    bankout_set_raw(a26 >> 13, false);
    sio_hw->gpio_togl = (sio_hw->gpio_out ^ (a26 & 0x1FFF)) & 0x1FFFu;
}
static void data_out(uint8_t v) { sio_hw->gpio_oe_set = DATA_MASK; sio_hw->gpio_togl = (sio_hw->gpio_out ^ ((uint32_t)v << DATA_SHIFT)) & DATA_MASK; }
static void data_in(void) { sio_hw->gpio_oe_clr = DATA_MASK; }
static inline void rw(bool read) { gpio_put(PIN_CPU_RW, read); }       /* read: flash /OE low (via 1G04), 245 direction irrelevant (isolated) */
static inline void romsel(bool active) { gpio_put(PIN_CPU_ROMSEL, !active); }

void nor_bus_take(void) {
    gpio_init(PIN_ISOLATE); gpio_set_dir(PIN_ISOLATE, true); gpio_put(PIN_ISOLATE, 1);
    for (uint g = 0; g < 15; g++) { gpio_init(g); gpio_set_dir(g, true); gpio_put(g, 0); }
    for (uint g = 15; g < 23; g++) { gpio_init(g); gpio_set_dir(g, false); }
    gpio_init(PIN_CPU_RW); gpio_set_dir(PIN_CPU_RW, true); gpio_put(PIN_CPU_RW, 1);
    gpio_init(PIN_CPU_M2); gpio_set_dir(PIN_CPU_M2, true); gpio_put(PIN_CPU_M2, 0);          /* M2 low: WRAM /WE idle */
    gpio_init(PIN_CPU_ROMSEL); gpio_set_dir(PIN_CPU_ROMSEL, true); gpio_put(PIN_CPU_ROMSEL, 1);
    gpio_init(PIN_PRG_NWE); gpio_set_dir(PIN_PRG_NWE, true); gpio_put(PIN_PRG_NWE, 1);
    gpio_put(PIN_WRAM_NCE, 1);
}
void nor_bus_release(void) {
    data_in();
    for (uint g = 0; g < 26; g++) { gpio_init(g); gpio_set_dir(g, false); }
    gpio_put(PIN_ISOLATE, 0);
}

/* ---- PRG flash primitives (word addresses = our byte addresses; upper data byte is pulled up to 0xFF) ---- */
static void wr(uint32_t a, uint8_t v) {
    set_addr(a); rw(false); data_out(v); romsel(true); dly(4);
    gpio_put(PIN_PRG_NWE, 0); dly(6); gpio_put(PIN_PRG_NWE, 1); dly(2);
    romsel(false); data_in(); rw(true);
}
static uint8_t rd(uint32_t a) {
    set_addr(a); data_in(); rw(true); romsel(true); dly(20);                 /* tCE 100 ns + buffers */
    uint8_t v = (uint8_t)(sio_hw->gpio_in >> DATA_SHIFT);
    romsel(false); return v;
}
uint8_t nor_prg_read(uint32_t addr) { return rd(addr); }
static void unlock(void) { wr(0x555, 0xAA); wr(0x2AA, 0x55); }
uint16_t nor_prg_id(uint8_t *mfr) {
    unlock(); wr(0x555, 0x90);
    uint8_t m = rd(0), d1 = rd(1), d2 = rd(0xE), d3 = rd(0xF);
    wr(0, 0xF0);
    if (mfr) *mfr = m;
    return (uint16_t)(d1 << 8 | d2) ^ (uint16_t)(d3 << 12 & 0);
}
static bool poll_done(uint32_t a, uint8_t expect, uint32_t timeout_us) {
    absolute_time_t t = make_timeout_time_us(timeout_us);
    for (;;) {
        uint8_t v = rd(a);
        if ((v & 0x80) == (expect & 0x80)) return true;           /* DQ7 = data when done */
        if (v & 0x20) { v = rd(a); if ((v & 0x80) == (expect & 0x80)) return true; return false; }   /* DQ5 timeout */
        if (time_reached(t)) return false;
    }
}
bool nor_prg_erase_sector(uint32_t addr) {
    uint32_t sa = addr & ~0x1FFFFu;
    unlock(); wr(0x555, 0x80); unlock(); wr(sa, 0x30);
    return poll_done(sa, 0xFF, 4000000);
}
bool nor_prg_program(uint32_t addr, const uint8_t *data, uint32_t len) {
    while (len) {
        uint32_t page_end = (addr | 0x1FF) + 1;                        /* 512-byte (256-word) write-buffer page */
        uint32_t n = page_end - addr; if (n > len) n = len;
        uint32_t sa = addr & ~0x1FFFFu;
        unlock(); wr(sa, 0x25); wr(sa, (uint8_t)(n - 1));
        for (uint32_t i = 0; i < n; i++) wr(addr + i, data[i]);
        wr(sa, 0x29);
        if (!poll_done(addr + n - 1, data[n - 1], 20000)) return false;
        addr += n; data += n; len -= n;
    }
    return true;
}
/* ---- F-RAM (WRAM) ---- */
void nor_wram_write(uint32_t addr, uint8_t v) {
    bankout_set_raw(addr >> 13, true);
    sio_hw->gpio_togl = (sio_hw->gpio_out ^ (addr & 0x1FFF)) & 0x1FFFu;
    rw(false); data_out(v); gpio_put(PIN_WRAM_NCE, 0); gpio_put(PIN_CPU_M2, 1); dly(10); gpio_put(PIN_CPU_M2, 0); dly(2);
    gpio_put(PIN_WRAM_NCE, 1); data_in(); rw(true);
}
uint8_t nor_wram_read(uint32_t addr) {
    bankout_set_raw(addr >> 13, true);
    sio_hw->gpio_togl = (sio_hw->gpio_out ^ (addr & 0x1FFF)) & 0x1FFFu;
    data_in(); rw(true); gpio_put(PIN_WRAM_NCE, 0); dly(14);
    uint8_t v = (uint8_t)(sio_hw->gpio_in >> DATA_SHIFT); gpio_put(PIN_WRAM_NCE, 1); return v;
}
/* ---- CHR flash through U2 + bridge ---- */
static bool chr_addr(uint32_t a, bool ram) {
    maplink_send(link_frame(LINK_T_CHR_ADDR_HI, ((a >> 24) & 3) | (ram ? 4 : 0)));
    maplink_send(link_frame(LINK_T_CHR_ADDR, a & 0xFFFFFF));
    return true;
}
static bool chr_wr(uint32_t a, uint8_t v) {
    chr_addr(a, false); data_out(v); dly(10);
    maplink_send(link_frame(LINK_T_CHR_WRITE, 0));
    bool ok = maplink_wait_ack(LINK_R_ACK, 20000);
    data_in(); return ok;
}
uint8_t nor_chr_read(uint32_t addr) {
    chr_addr(addr, false); data_in();
    maplink_send(link_frame(LINK_T_CHR_READ, 0)); maplink_wait_ack(LINK_R_ACK, 20000); dly(20);
    uint8_t v = (uint8_t)(sio_hw->gpio_in >> DATA_SHIFT);
    maplink_send(link_frame(LINK_T_CHR_READ_END, 0)); maplink_wait_ack(LINK_R_ACK, 20000);
    return v;
}
static bool chr_poll(uint32_t a, uint8_t expect, uint32_t timeout_us) {
    absolute_time_t t = make_timeout_time_us(timeout_us);
    for (;;) { uint8_t v = nor_chr_read(a); if ((v & 0x80) == (expect & 0x80)) return true; if (time_reached(t)) return false; }
}
bool nor_chr_begin(void) { maplink_send(link_frame(LINK_T_CMD, (LINK_C_ISOLATE << 16) | 1)); return maplink_wait_ack(LINK_R_ACK, 100000); }
void nor_chr_end(void) { maplink_send(link_frame(LINK_T_CMD, (LINK_C_ISOLATE << 16) | 0)); maplink_wait_ack(LINK_R_ACK, 100000); }
bool nor_chr_erase_sector(uint32_t addr) {
    uint32_t sa = addr & ~0x1FFFFu;
    chr_wr(0x555, 0xAA); chr_wr(0x2AA, 0x55); chr_wr(0x555, 0x80); chr_wr(0x555, 0xAA); chr_wr(0x2AA, 0x55); chr_wr(sa, 0x30);
    return chr_poll(sa, 0xFF, 4000000);
}
bool nor_chr_program(uint32_t addr, const uint8_t *data, uint32_t len) {
    while (len) {
        uint32_t page_end = (addr | 0x1FF) + 1; uint32_t n = page_end - addr; if (n > len) n = len;
        uint32_t sa = addr & ~0x1FFFFu;
        chr_wr(0x555, 0xAA); chr_wr(0x2AA, 0x55); chr_wr(sa, 0x25); chr_wr(sa, (uint8_t)(n - 1));
        for (uint32_t i = 0; i < n; i++) if (!chr_wr(addr + i, data[i])) return false;
        chr_wr(sa, 0x29);
        if (!chr_poll(addr + n - 1, data[n - 1], 20000)) return false;
        addr += n; data += n; len -= n;
    }
    return true;
}
