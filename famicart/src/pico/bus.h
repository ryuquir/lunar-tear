#pragma once
#include "../core/cart.h"
void bus_init(cart_t *c);          /* configures PIO, launches core1 (PPU), enables the CPU-bus IRQ on core0 */
void bus_stop(void);
extern volatile uint32_t bus_stat_cpu_cycles, bus_stat_cpu_reads, bus_stat_cpu_writes, bus_stat_ppu_reads, bus_stat_ppu_writes, bus_stat_late;
