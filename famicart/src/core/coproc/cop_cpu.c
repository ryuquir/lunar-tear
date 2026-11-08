#include "cop_cpu.h"
#include <string.h>

void cop_cpu_reset(cop_cpu_t *c) { memset(c, 0, sizeof *c); c->regs[COP_R_STATUS] = COP_ABI_VERSION; }
uint8_t cop_cpu_read(const cop_cpu_t *c, uint16_t off) {
    if (off < COP_R_SRAM) return c->regs[off];
    if (off < COP_R_SRAM + COP_SRAM_SIZE) return c->sram[off - COP_R_SRAM];
    return 0;
}
void cop_cpu_write(cop_cpu_t *c, uint16_t off, uint8_t v) {
    if (off == COP_R_CMD) { c->regs[COP_R_CMD] = v; c->regs[COP_R_STATUS] = COP_ST_BUSY | COP_ABI_VERSION; c->pending = 1; return; }
    if (off == COP_R_STATUS) return;
    if (off < COP_R_SRAM) { c->regs[off] = v; return; }
    if (off < COP_R_SRAM + COP_SRAM_SIZE) c->sram[off - COP_R_SRAM] = v;
}

/* quarter-wave sine table, s1.14, 65 entries (0..90 degrees in 64 steps) */
static const int16_t qsin[65] = {
    0, 402, 804, 1205, 1606, 2006, 2404, 2801, 3196, 3590, 3981, 4370, 4756, 5139, 5520, 5897,
    6270, 6639, 7005, 7366, 7723, 8076, 8423, 8765, 9102, 9434, 9760, 10080, 10394, 10702, 11003, 11297,
    11585, 11866, 12140, 12406, 12665, 12916, 13160, 13395, 13623, 13842, 14053, 14256, 14449, 14635, 14811, 14978,
    15137, 15286, 15426, 15557, 15679, 15791, 15893, 15986, 16069, 16143, 16207, 16261, 16305, 16340, 16364, 16379, 16384 };
int16_t cop_sin14(uint8_t a) {
    unsigned q = a >> 6, i = a & 63;
    switch (q) { case 0: return qsin[i]; case 1: return qsin[64 - i]; case 2: return (int16_t)-qsin[i]; default: return (int16_t)-qsin[64 - i]; }
}
static uint16_t g16(const uint8_t *r, unsigned i) { return (uint16_t)(r[i] | (r[i + 1] << 8)); }
static uint32_t g32(const uint8_t *r, unsigned i) { return (uint32_t)g16(r, i) | ((uint32_t)g16(r, i + 2) << 16); }
static void p16(uint8_t *r, unsigned i, uint16_t v) { r[i] = (uint8_t)v; r[i + 1] = (uint8_t)(v >> 8); }
static void p32(uint8_t *r, unsigned i, uint32_t v) { p16(r, i, (uint16_t)v); p16(r, i + 2, (uint16_t)(v >> 16)); }

bool cop_cpu_run(cop_cpu_t *c) {
    if (!c->pending) return false;
    c->pending = 0;
    uint8_t *a = c->regs + COP_R_ARG, st = COP_ABI_VERSION;
    switch (c->regs[COP_R_CMD]) {
    case COP_C_NOP: break;
    case COP_C_MUL16:
        if (a[8] & 1) p32(a, 4, (uint32_t)((int32_t)(int16_t)g16(a, 0) * (int32_t)(int16_t)g16(a, 2)));
        else p32(a, 4, (uint32_t)g16(a, 0) * g16(a, 2));
        break;
    case COP_C_DIV32: {
        uint32_t n = g32(a, 0); uint16_t d = g16(a, 4);
        if (!d) { st |= COP_ST_ERROR; break; }
        p32(a, 6, n / d); p16(a, 10, (uint16_t)(n % d)); break; }
    case COP_C_MEMSET: {
        uint16_t off = g16(a, 0), len = g16(a, 2);
        if ((uint32_t)off + len > COP_SRAM_SIZE) { st |= COP_ST_ERROR; break; }
        memset(c->sram + off, a[4], len); break; }
    case COP_C_MEMCPY: {
        uint16_t d = g16(a, 0), s = g16(a, 2), len = g16(a, 4);
        if ((uint32_t)d + len > COP_SRAM_SIZE || (uint32_t)s + len > COP_SRAM_SIZE) { st |= COP_ST_ERROR; break; }
        memmove(c->sram + d, c->sram + s, len); break; }
    case COP_C_SINCOS: p16(a, 2, (uint16_t)cop_sin14(a[0])); p16(a, 4, (uint16_t)cop_sin14((uint8_t)(a[0] + 64))); break;
    case COP_C_ROT2D: {
        int32_t x = (int16_t)g16(a, 0), y = (int16_t)g16(a, 2), s = cop_sin14(a[4]), co = cop_sin14((uint8_t)(a[4] + 64));
        p16(a, 6, (uint16_t)(int16_t)((x * co - y * s) >> 14)); p16(a, 8, (uint16_t)(int16_t)((x * s + y * co) >> 14)); break; }
    default: st |= COP_ST_ERROR; break;
    }
    c->regs[COP_R_STATUS] = st;                                  /* busy cleared last */
    return true;
}
