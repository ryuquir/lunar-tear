/* rev D, U1 bus front-end: snoop every M2 cycle on the local CPU bus, serve $4020-$5FFF reads ourselves
 * (mapper registers, ExRAM, boot-stub flags), forward register writes to the mapper core and to U2. */
#include "bus_revd.h"
#include "bankout.h"
#include "maplink.h"
#include "board.h"
#include "../core/mapper.h"
#include "../core/audio/expaudio.h"
#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "hardware/pio.h"
#include "hardware/irq.h"
#include "hardware/gpio.h"
#include "hardware/structs/sio.h"
#include "fc_bus_revd.pio.h"

volatile uint32_t bus_stat_cpu_cycles, bus_stat_cpu_reads, bus_stat_cpu_writes, bus_stat_resets;
static cart_t *g_cart;
static PIO pio_cpu = pio0; static uint sm_cpu;
static volatile uint8_t boot_ready = 0, boot_cmd = 0;
#define RSP_NONE      0u
#define RSP_DRIVE(d)  (1u | ((uint32_t)(d) << 1))
#define RSP_CAPTURE   2u

void busd_boot_flags(uint8_t ready, uint8_t cmd) { boot_ready = ready; boot_cmd = cmd; }
FC_INLINE void irq_pin_set(bool assert_low) { if (assert_low) sio_hw->gpio_hi_clr = 1u << (PIN_IRQ - 32); else sio_hw->gpio_hi_set = 1u << (PIN_IRQ - 32); }

static void __not_in_flash_func(cpu_isr)(void) {
    cart_t *c = g_cart;
    static uint8_t awaiting_write; static uint16_t waddr; static uint8_t last_ffc;
    while (!pio_sm_is_rx_fifo_empty(pio_cpu, sm_cpu)) {
        uint32_t w = pio_sm_get(pio_cpu, sm_cpu);     /* bits: 0-14 A, 15-22 D, 23 R/W, 24 M2, 25 /ROMSEL */
        if (awaiting_write) {
            awaiting_write = 0;
            uint8_t v = (uint8_t)(w >> 15);
            cart_cpu_write(c, waddr, v);
            if (c->tables_dirty) bankout_update(c);
            maplink_send_try(link_frame(LINK_T_CPU_WRITE, ((uint32_t)waddr << 8) | v));
            bus_stat_cpu_writes++;
            irq_pin_set(c->irq_line);
            continue;
        }
        bool rw = (w >> 23) & 1, romsel_n = (w >> 25) & 1;
        uint16_t addr = (uint16_t)((w & 0x7FFF) | (romsel_n ? 0 : 0x8000));
        bus_stat_cpu_cycles++;
        if (rw) {
            if (addr >= 0x4020 && addr < 0x6000) {
                uint8_t v; bool have = false;
                if (addr == 0x5F00) { v = boot_ready ? 0xA5 : 0x00; have = true; }
                else if (addr == 0x5F01) { v = boot_cmd; have = true; if (boot_cmd == 1) { bankout_go(true); } }
                else if (c->mapper && c->has_read_hook) { v = c->mapper->read(c, addr, c->open_bus); have = true; maplink_send_try(link_frame(LINK_T_CPU_READ, addr)); }
                if (have) { pio_sm_put(pio_cpu, sm_cpu, RSP_DRIVE(v)); c->open_bus = v; bus_stat_cpu_reads++; }
                else pio_sm_put(pio_cpu, sm_cpu, RSP_NONE);
            } else {
                pio_sm_put(pio_cpu, sm_cpu, RSP_NONE);
                if (addr == 0xFFFC) last_ffc = 1; else if (addr == 0xFFFD && last_ffc) { bus_stat_resets++; last_ffc = 0; } else last_ffc = 0;
            }
        } else {
            if (addr >= 0x4020 || (c->mapper && (c->mapper->flags & MF_SNOOP_PPU_REGS))) { pio_sm_put(pio_cpu, sm_cpu, RSP_CAPTURE); awaiting_write = 1; waddr = addr; }
            else pio_sm_put(pio_cpu, sm_cpu, RSP_NONE);
        }
        c->cpu_cycles++;
        if (c->has_cpu_cycle_hook) c->mapper->cpu_cycle(c);
        irq_pin_set(c->irq_line);
    }
}

void busd_init(cart_t *c) {
    g_cart = c;
    for (uint g = PIN_CPU_BASE; g < PIN_CPU_BASE + 26; g++) { pio_gpio_init(pio_cpu, g); gpio_set_input_hysteresis_enabled(g, true); gpio_set_slew_rate(g, GPIO_SLEW_RATE_FAST); }
    pio_gpio_init(pio_cpu, PIN_NDRIVE);
    gpio_init(PIN_IRQ); gpio_set_dir(PIN_IRQ, true); gpio_put(PIN_IRQ, 1);
    uint off = pio_add_program(pio_cpu, &fc_cpu_revd_program);
    sm_cpu = pio_claim_unused_sm(pio_cpu, true);
    pio_sm_config cfg = fc_cpu_revd_program_get_default_config(off);
    sm_config_set_in_pins(&cfg, PIN_CPU_BASE);
    sm_config_set_out_pins(&cfg, PIN_CPU_DATA_BASE, 8);
    sm_config_set_sideset_pins(&cfg, PIN_NDRIVE);
    sm_config_set_in_shift(&cfg, false, false, 32);
    sm_config_set_out_shift(&cfg, true, false, 32);
    pio_sm_set_consecutive_pindirs(pio_cpu, sm_cpu, PIN_CPU_BASE, 26, false);
    pio_sm_set_pins_with_mask64(pio_cpu, sm_cpu, 1ull << PIN_NDRIVE, 1ull << PIN_NDRIVE);
    pio_sm_set_consecutive_pindirs(pio_cpu, sm_cpu, PIN_NDRIVE, 1, true);
    pio_sm_init(pio_cpu, sm_cpu, off, &cfg);
    uint irqn = PIO0_IRQ_0;
    pio_set_irq0_source_enabled(pio_cpu, (enum pio_interrupt_source)(pis_sm0_rx_fifo_not_empty + sm_cpu), true);
    irq_set_exclusive_handler(irqn, cpu_isr); irq_set_priority(irqn, 0); irq_set_enabled(irqn, true);
    pio_sm_set_enabled(pio_cpu, sm_cpu, true);
    multicore_launch_core1(bankout_core1);
}
void busd_stop(void) {
    pio_sm_set_enabled(pio_cpu, sm_cpu, false); irq_set_enabled(PIO0_IRQ_0, false);
    multicore_reset_core1();
    for (uint g = PIN_CPU_BASE; g < PIN_CPU_BASE + 26; g++) gpio_init(g);   /* back to SIO, inputs */
    gpio_init(PIN_NDRIVE); gpio_set_dir(PIN_NDRIVE, true); gpio_put(PIN_NDRIVE, 1);
}
