/* PPU-side coprocessor (rev F U5): draws into CHR memory in the NES 2 bpp planar format. Portable. */
#pragma once
#include "cop_abi.h"
typedef struct {
    uint8_t *chr; uint32_t size;      /* owned CHR bytes (4 KB per buffer) */
    uint8_t buf;                      /* draw buffer */
    uint8_t cmd, arg[14];
    volatile uint8_t pending, busy;
} cop_ppu_t;
void cop_ppu_reset(cop_ppu_t *p, uint8_t *chr, uint32_t size);
void cop_ppu_write(cop_ppu_t *p, uint16_t off, uint8_t v);      /* off = addr - base, 0x3F0 .. 0x3FE */
bool cop_ppu_run(cop_ppu_t *p);
void cop_ppu_plot(cop_ppu_t *p, int x, int y, unsigned color);
unsigned cop_ppu_pixel(const cop_ppu_t *p, int x, int y);
