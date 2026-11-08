/* Bandai LZ93D50 + 24C02 (mapper 16 sub 5) / 24C01 (159): multi-byte EEPROM write + read back through $800D/$6000. */
#include "tm_util.h"
extern const mapper_desc_t mapper_016, mapper_159;
static cart_t c;
static void set(int scl, int sda) { cart_cpu_write(&c, 0x800D, (uint8_t)((scl << 5) | (sda << 6))); }
static int sda_in(void) { c.open_bus = 0; return (cart_cpu_read(&c, 0x6000) >> 4) & 1; }
static void start(void) { set(1, 1); set(1, 0); set(0, 0); }
static void stop(void) { set(0, 0); set(1, 0); set(1, 1); }
static bool wbyte(uint8_t b) {
    for (int i = 7; i >= 0; i--) { int d = (b >> i) & 1; set(0, d); set(1, d); set(0, d); }
    set(0, 1); set(1, 1); bool ack = !sda_in(); set(0, 1);
    return ack;
}
static uint8_t rbyte(bool ack) {
    uint8_t b = 0;
    for (int i = 0; i < 8; i++) { set(0, 1); set(1, 1); b = (uint8_t)((b << 1) | sda_in()); }
    set(0, ack ? 0 : 1); set(1, ack ? 0 : 1); set(0, ack ? 0 : 1);
    return b;
}
void tm_bandai_ee(int *checks, int *fails) {
    TM_CHECK(tm_load(&c, &mapper_016, 5, 256, 256, 0, 0, 1), "16/5 load");
    start(); TM_CHECK(wbyte(0xA0) && wbyte(0x10) && wbyte(0x11) && wbyte(0x22) && wbyte(0x33), "24C02 sequential write acks"); stop();
    start(); wbyte(0xA0); wbyte(0x10); start(); TM_CHECK(wbyte(0xA1), "24C02 read select");
    uint8_t a = rbyte(true), b = rbyte(true), d = rbyte(false); stop();
    TM_CHECK(a == 0x11 && b == 0x22 && d == 0x33, "24C02 read back %02X %02X %02X", a, b, d);
    TM_CHECK(tm_load(&c, &mapper_159, 0, 256, 256, 0, 0, 1), "159 load");
    start(); TM_CHECK(wbyte(0x05 << 1) && wbyte(0x44) && wbyte(0x55), "24C01 sequential write acks"); stop();
    start(); TM_CHECK(wbyte((0x05 << 1) | 1), "24C01 read select");
    a = rbyte(true); b = rbyte(false); stop();
    TM_CHECK(a == 0x44 && b == 0x55, "24C01 read back %02X %02X", a, b);
}
