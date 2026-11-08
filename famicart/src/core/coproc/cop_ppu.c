#include "cop_ppu.h"
#include <string.h>
#include <stdlib.h>

void cop_ppu_reset(cop_ppu_t *p, uint8_t *chr, uint32_t size) { memset(p, 0, sizeof *p); p->chr = chr; p->size = size; }
void cop_ppu_write(cop_ppu_t *p, uint16_t off, uint8_t v) {
    if (off == COP_R_PPU_CMD) { p->cmd = v; p->pending = 1; p->busy = 1; }
    else if (off > COP_R_PPU_CMD && off < COP_R_PPU_STATUS) p->arg[off - COP_R_PPU_ARG] = v;
}
static inline uint8_t *bufp(const cop_ppu_t *p) { uint32_t o = (uint32_t)p->buf * 4096u; return (o + 4096u <= p->size) ? p->chr + o : NULL; }
void cop_ppu_plot(cop_ppu_t *p, int x, int y, unsigned color) {
    uint8_t *b = bufp(p);
    if (!b || x < 0 || y < 0 || x > 127 || y > 127) return;
    uint8_t *t = b + ((unsigned)(y >> 3) * 16u + (unsigned)(x >> 3)) * 16u + (unsigned)(y & 7);
    uint8_t m = (uint8_t)(0x80u >> (x & 7));
    if (color & 1) t[0] |= m; else t[0] &= (uint8_t)~m;
    if (color & 2) t[8] |= m; else t[8] &= (uint8_t)~m;
}
unsigned cop_ppu_pixel(const cop_ppu_t *p, int x, int y) {
    const uint8_t *b = bufp(p);
    if (!b || x < 0 || y < 0 || x > 127 || y > 127) return 0;
    const uint8_t *t = b + ((unsigned)(y >> 3) * 16u + (unsigned)(x >> 3)) * 16u + (unsigned)(y & 7);
    uint8_t m = (uint8_t)(0x80u >> (x & 7));
    return ((t[0] & m) ? 1u : 0u) | ((t[8] & m) ? 2u : 0u);
}
static void line(cop_ppu_t *p, int x0, int y0, int x1, int y1, unsigned c) {
    int dx = abs(x1 - x0), sx = x0 < x1 ? 1 : -1, dy = -abs(y1 - y0), sy = y0 < y1 ? 1 : -1, e = dx + dy;
    for (;;) {
        cop_ppu_plot(p, x0, y0, c);
        if (x0 == x1 && y0 == y1) break;
        int e2 = 2 * e;
        if (e2 >= dy) { e += dy; x0 += sx; }
        if (e2 <= dx) { e += dx; y0 += sy; }
    }
}
bool cop_ppu_run(cop_ppu_t *p) {
    if (!p->pending) return false;
    p->pending = 0;
    const uint8_t *a = p->arg;
    switch (p->cmd) {
    case COP_P_CLEAR: { uint8_t *b = bufp(p); if (b) { uint8_t lo = (a[0] & 1) ? 0xFF : 0, hi = (a[0] & 2) ? 0xFF : 0;
                        for (unsigned t = 0; t < 256; t++) { memset(b + t * 16, lo, 8); memset(b + t * 16 + 8, hi, 8); } } break; }
    case COP_P_PLOT: cop_ppu_plot(p, a[0], a[1], a[2]); break;
    case COP_P_LINE: line(p, a[0], a[1], a[2], a[3], a[4]); break;
    case COP_P_RECT: for (int y = a[1]; y < a[1] + a[3]; y++) for (int x = a[0]; x < a[0] + a[2]; x++) cop_ppu_plot(p, x, y, a[4]); break;
    case COP_P_SELECT: p->buf = a[0] & 1; break;
    default: break;
    }
    p->busy = 0;
    return true;
}
