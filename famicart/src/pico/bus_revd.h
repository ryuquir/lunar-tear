#pragma once
#include "../core/cart.h"
#include <stdint.h>
extern volatile uint32_t bus_stat_cpu_cycles, bus_stat_cpu_reads, bus_stat_cpu_writes, bus_stat_resets;
void busd_init(cart_t *c);                 /* start the PIO snoop + ISR; bank lines stay in boot state until bankout_go(true) */
void busd_stop(void);                      /* stop PIO/ISR (programming mode) */
void busd_boot_flags(uint8_t ready, uint8_t cmd);   /* what the boot stub reads at $5F00 / $5F01 */
