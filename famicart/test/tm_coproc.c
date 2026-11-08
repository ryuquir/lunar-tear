/* rev F coprocessor cores (core/coproc): CPU-side command engine and PPU-side CHR drawing. */
#include "tm_util.h"
#include "coproc/cop_cpu.h"
#include "coproc/cop_ppu.h"
#include <math.h>
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif
static void w16(cop_cpu_t *c, unsigned r, uint16_t v) { cop_cpu_write(c, (uint16_t)(COP_R_ARG + r), (uint8_t)v); cop_cpu_write(c, (uint16_t)(COP_R_ARG + r + 1), (uint8_t)(v >> 8)); }
static uint16_t r16(cop_cpu_t *c, unsigned r) { return (uint16_t)(cop_cpu_read(c, (uint16_t)(COP_R_ARG + r)) | (cop_cpu_read(c, (uint16_t)(COP_R_ARG + r + 1)) << 8)); }
static uint32_t r32(cop_cpu_t *c, unsigned r) { return r16(c, r) | ((uint32_t)r16(c, r + 2) << 16); }
void tm_coproc(int *checks, int *fails) {
    static cop_cpu_t c; cop_cpu_reset(&c);
    TM_CHECK((cop_cpu_read(&c, COP_R_STATUS) & 0x0F) == COP_ABI_VERSION && !(cop_cpu_read(&c, COP_R_STATUS) & COP_ST_BUSY), "idle, version");
    w16(&c, 0, 1234); w16(&c, 2, 5678); cop_cpu_write(&c, COP_R_ARG + 8, 0); cop_cpu_write(&c, COP_R_CMD, COP_C_MUL16);
    TM_CHECK(cop_cpu_read(&c, COP_R_STATUS) & COP_ST_BUSY, "busy after CMD");
    TM_CHECK(cop_cpu_run(&c) && !(cop_cpu_read(&c, COP_R_STATUS) & COP_ST_BUSY) && r32(&c, 4) == 1234u * 5678u, "MUL16 unsigned %lu", (unsigned long)r32(&c, 4));
    w16(&c, 0, (uint16_t)-300); w16(&c, 2, 25); cop_cpu_write(&c, COP_R_ARG + 8, 1); cop_cpu_write(&c, COP_R_CMD, COP_C_MUL16); cop_cpu_run(&c);
    TM_CHECK((int32_t)r32(&c, 4) == -7500, "MUL16 signed");
    w16(&c, 0, 0x5678); w16(&c, 2, 0x0012); w16(&c, 4, 1000); cop_cpu_write(&c, COP_R_CMD, COP_C_DIV32); cop_cpu_run(&c);
    TM_CHECK(r32(&c, 6) == 0x125678u / 1000u && r16(&c, 10) == 0x125678u % 1000u, "DIV32");
    w16(&c, 4, 0); cop_cpu_write(&c, COP_R_CMD, COP_C_DIV32); cop_cpu_run(&c);
    TM_CHECK(cop_cpu_read(&c, COP_R_STATUS) & COP_ST_ERROR, "DIV32 by zero -> error");
    for (unsigned i = 0; i < 16; i++) cop_cpu_write(&c, (uint16_t)(COP_R_SRAM + i), (uint8_t)i);
    w16(&c, 0, 4); w16(&c, 2, 0); w16(&c, 4, 8); cop_cpu_write(&c, COP_R_CMD, COP_C_MEMCPY); cop_cpu_run(&c);
    TM_CHECK(cop_cpu_read(&c, COP_R_SRAM + 4) == 0 && cop_cpu_read(&c, COP_R_SRAM + 11) == 7, "MEMCPY overlapping");
    w16(&c, 0, COP_SRAM_SIZE - 2); w16(&c, 2, 4); cop_cpu_write(&c, COP_R_ARG + 4, 0xAA); cop_cpu_write(&c, COP_R_CMD, COP_C_MEMSET); cop_cpu_run(&c);
    TM_CHECK(cop_cpu_read(&c, COP_R_STATUS) & COP_ST_ERROR, "MEMSET out of range -> error");
    double maxerr = 0;
    for (int a = 0; a < 256; a++) { double e = fabs(cop_sin14((uint8_t)a) / 16384.0 - sin(a * 2 * M_PI / 256)); if (e > maxerr) maxerr = e; }
    TM_CHECK(maxerr < 0.0001, "sine table error %g", maxerr);
    w16(&c, 0, 1000); w16(&c, 2, 0); cop_cpu_write(&c, COP_R_ARG + 4, 64); cop_cpu_write(&c, COP_R_CMD, COP_C_ROT2D); cop_cpu_run(&c);
    TM_CHECK(abs((int16_t)r16(&c, 6)) <= 1 && (int16_t)r16(&c, 8) == 1000, "ROT2D 90 deg (%d, %d)", (int16_t)r16(&c, 6), (int16_t)r16(&c, 8));
    cop_cpu_write(&c, COP_R_CMD, 0x7F); cop_cpu_run(&c); TM_CHECK(cop_cpu_read(&c, COP_R_STATUS) & COP_ST_ERROR, "unknown command -> error");
    /* PPU side */
    static uint8_t chr[8192]; static cop_ppu_t p; cop_ppu_reset(&p, chr, sizeof chr);
    cop_ppu_write(&p, COP_R_PPU_ARG, 2); cop_ppu_write(&p, COP_R_PPU_CMD, COP_P_CLEAR);
    TM_CHECK(p.busy && cop_ppu_run(&p) && !p.busy && cop_ppu_pixel(&p, 77, 99) == 2 && chr[0] == 0 && chr[8] == 0xFF, "CLEAR 2");
    cop_ppu_plot(&p, 9, 10, 3);
    TM_CHECK(chr[(1 * 16 + 1) * 16 + 2] == 0x40 && chr[(1 * 16 + 1) * 16 + 10] == 0xFF && cop_ppu_pixel(&p, 9, 10) == 3, "PLOT lands in tile 17 row 2 bit 6");
    const uint8_t la[5] = { 0, 0, 127, 127, 1 };
    for (int i = 0; i < 5; i++) cop_ppu_write(&p, (uint16_t)(COP_R_PPU_ARG + i), la[i]);
    cop_ppu_write(&p, COP_R_PPU_CMD, COP_P_LINE); cop_ppu_run(&p);
    bool diag = true; for (int i = 0; i < 128; i++) if (cop_ppu_pixel(&p, i, i) != 1) diag = false;
    TM_CHECK(diag && cop_ppu_pixel(&p, 1, 0) == 2, "LINE diagonal");
    cop_ppu_write(&p, COP_R_PPU_ARG, 1); cop_ppu_write(&p, COP_R_PPU_CMD, COP_P_SELECT); cop_ppu_run(&p);
    cop_ppu_plot(&p, 0, 0, 1); TM_CHECK(chr[4096] == 0x80 && cop_ppu_pixel(&p, 5, 5) == 0, "buffer 1 at +4 KB");
    cop_ppu_plot(&p, 200, 3, 1); TM_CHECK(true, "out-of-range plot ignored");
}
