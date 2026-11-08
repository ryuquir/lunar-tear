/* CPU-side coprocessor (rev F U4): register window + shared SRAM + command engine. Portable. */
#pragma once
#include "cop_abi.h"
typedef struct {
    uint8_t regs[16];
    uint8_t sram[COP_SRAM_SIZE];
    volatile uint8_t pending;        /* command written, not yet run */
} cop_cpu_t;
void    cop_cpu_reset(cop_cpu_t *c);
uint8_t cop_cpu_read(const cop_cpu_t *c, uint16_t off);        /* off = addr - base, 0 .. 0x3EF */
void    cop_cpu_write(cop_cpu_t *c, uint16_t off, uint8_t v);
bool    cop_cpu_run(cop_cpu_t *c);                               /* run the pending command; true if one ran */
int16_t cop_sin14(uint8_t angle);                                /* s1.14 */
