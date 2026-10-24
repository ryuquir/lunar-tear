/* Bus front-end: PIO capture + core0 ISR (CPU) + core1 spin loop (PPU). */
#include "bus.h"
#include "board.h"
#include "../core/mapper.h"
#include "../core/audio/expaudio.h"
#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "hardware/pio.h"
#include "hardware/irq.h"
#include "hardware/gpio.h"
#include "hardware/sync.h"
#include "hardware/structs/sio.h"
#if FC_BUS_DIRECT
#include "fc_bus_direct.pio.h"
#else
#include "fc_bus.pio.h"
#endif

volatile uint32_t bus_stat_cpu_cycles, bus_stat_cpu_reads, bus_stat_cpu_writes, bus_stat_ppu_reads, bus_stat_ppu_writes, bus_stat_late;

#if FC_BUS_CAPABLE && !FC_BUS_DIRECT
_Static_assert(PIN_CPU_M2 == 17, "fc_bus.pio hardcodes 'wait gpio 17' for M2; update both");
_Static_assert(PIN_PPU_ACC == 16, "fc_bus.pio hardcodes 'wait gpio 16' for /PPUACC; update both");

static cart_t *g_cart;
static PIO pio_cpu = pio0, pio_ppu = pio1;
static uint sm_cpu = 0, sm_ppu = 0;

/* -------- response word helpers -------- */
#define RSP_NONE      0u
#define RSP_DRIVE(d)  (1u | ((uint32_t)(d) << 1))
#define RSP_CAPTURE   2u

FC_INLINE void irq_pin_set(bool assert_low) {
    /* 74LVC1G07 open-drain buffer on the board: GPIO low -> /IRQ pulled low, GPIO high -> released */
    if (assert_low) sio_hw->gpio_clr = 1u << PIN_IRQ; else sio_hw->gpio_set = 1u << PIN_IRQ;
}

/* -------- CPU bus ISR (core0) -------- */
static void FC_FASTCODE(cpu_bus_isr)(void) {
    cart_t *c = g_cart;
    static uint8_t awaiting_write; static uint16_t waddr;
    while (!pio_sm_is_rx_fifo_empty(pio_cpu, sm_cpu)) {
        uint32_t w = pio_sm_get(pio_cpu, sm_cpu);
        if (awaiting_write) {
            awaiting_write = 0;
            uint8_t v = (uint8_t)w;
            cart_cpu_write(c, waddr, v);
            bus_stat_cpu_writes++;
            irq_pin_set(c->irq_line);
            continue;
        }
        /* word = CTRL<<16 | AHI<<8 | ALO  (ISR shifts left) */
        bool rw       = (w >> (16 + CPU_CTRL_RW_BIT)) & 1;        /* 1 = read */
        bool romsel_n = (w >> (16 + CPU_CTRL_ROMSEL_BIT)) & 1;    /* 1 = /ROMSEL high = not $8000-$FFFF */
        uint16_t addr = (uint16_t)((w & 0xFF) | ((w >> 8) & 0x7F) << 8 | (romsel_n ? 0 : 0x8000));
        bus_stat_cpu_cycles++;
        if (rw) {
            if (addr >= 0x4020) {
                const uint8_t *p = c->prg_map[addr >> 13];
                uint8_t v;
                if (p) v = p[addr & 0x1FFF];
                else if (c->has_read_hook) v = c->mapper->read(c, addr, c->open_bus);
                else { pio_sm_put(pio_cpu, sm_cpu, RSP_NONE); goto tail; }
                if (!p && !(c->has_read_hook)) { pio_sm_put(pio_cpu, sm_cpu, RSP_NONE); goto tail; }
                /* only drive when the address is really ours: ROM/RAM mapped or mapper register */
                pio_sm_put(pio_cpu, sm_cpu, RSP_DRIVE(v));
                c->open_bus = v; bus_stat_cpu_reads++;
            } else pio_sm_put(pio_cpu, sm_cpu, RSP_NONE);
        } else {
            if (addr >= 0x4020 || (c->mapper->flags & MF_SNOOP_PPU_REGS)) { pio_sm_put(pio_cpu, sm_cpu, RSP_CAPTURE); awaiting_write = 1; waddr = addr; }
            else pio_sm_put(pio_cpu, sm_cpu, RSP_NONE);
        }
    tail:
        c->cpu_cycles++;
        if (c->has_cpu_cycle_hook) c->mapper->cpu_cycle(c);
        irq_pin_set(c->irq_line);
    }
}

/* -------- PPU bus loop (core1, never returns) -------- */
static void FC_FASTCODE(ppu_bus_core1)(void) {
    cart_t *c = g_cart;
    const uint32_t ce_mask = 1u << PIN_CIRAM_CE, a10_mask = 1u << PIN_CIRAM_A10;
    for (;;) {
        uint32_t w = pio_sm_get_blocking(pio_ppu, sm_ppu);
        uint16_t addr = (uint16_t)(w & 0x3FFF);
        bool rd_n = (w >> 14) & 1, wr_n = (w >> 15) & 1;
        if (c->has_ppu_hook) { c->ppu_override = NULL; c->mapper->ppu_addr(c, addr); }
        if (addr < 0x2000) {
            sio_hw->gpio_set = ce_mask;                       /* CIRAM off */
            if (!rd_n) {
                uint8_t v = c->ppu_override ? *c->ppu_override : c->chr_map[addr >> 10][addr & 0x3FF];
                pio_sm_put(pio_ppu, sm_ppu, RSP_DRIVE(v)); bus_stat_ppu_reads++;
            } else if (!wr_n) {
                pio_sm_put(pio_ppu, sm_ppu, RSP_CAPTURE);
                uint8_t v = (uint8_t)pio_sm_get_blocking(pio_ppu, sm_ppu);
                if (c->chr_wmask & (1u << (addr >> 10))) c->chr_map[addr >> 10][addr & 0x3FF] = v;
                bus_stat_ppu_writes++;
            } else pio_sm_put(pio_ppu, sm_ppu, RSP_NONE);
        } else if (addr < 0x3F00) {
            unsigned nt = (addr >> 10) & 3;
            uint8_t *p = c->nt_map[nt];
            if (!p) {   /* console CIRAM: select bank, enable, and stay off the data bus */
                if (c->nt_ciram_a10[nt]) sio_hw->gpio_set = a10_mask; else sio_hw->gpio_clr = a10_mask;
                sio_hw->gpio_clr = ce_mask;
                if (!rd_n && c->ppu_override) pio_sm_put(pio_ppu, sm_ppu, RSP_DRIVE(*c->ppu_override)), sio_hw->gpio_set = ce_mask;
                else pio_sm_put(pio_ppu, sm_ppu, RSP_NONE);
            } else {
                sio_hw->gpio_set = ce_mask;
                if (!rd_n) pio_sm_put(pio_ppu, sm_ppu, RSP_DRIVE(c->ppu_override ? *c->ppu_override : p[addr & 0x3FF]));
                else if (!wr_n) { pio_sm_put(pio_ppu, sm_ppu, RSP_CAPTURE); p[addr & 0x3FF] = (uint8_t)pio_sm_get_blocking(pio_ppu, sm_ppu); }
                else pio_sm_put(pio_ppu, sm_ppu, RSP_NONE);
            }
        } else { sio_hw->gpio_set = ce_mask; pio_sm_put(pio_ppu, sm_ppu, RSP_NONE); }   /* palette: internal to the PPU */
    }
}

static void port_init(PIO pio, uint sm, uint prog_offset, const pio_program_t *prog, uint port_base, uint in_count, uint sel_base) {
    pio_sm_config cfg = (prog == &fc_cpu_program) ? fc_cpu_program_get_default_config(prog_offset) : fc_ppu_program_get_default_config(prog_offset);
    for (uint i = 0; i < 8; i++) { pio_gpio_init(pio, port_base + i); gpio_set_input_hysteresis_enabled(port_base + i, true); }
    if (in_count > 8) pio_gpio_init(pio, port_base + 8);
    pio_gpio_init(pio, sel_base); pio_gpio_init(pio, sel_base + 1);
    gpio_set_slew_rate(sel_base, GPIO_SLEW_RATE_FAST); gpio_set_slew_rate(sel_base + 1, GPIO_SLEW_RATE_FAST);
    for (uint i = 0; i < 8; i++) gpio_set_slew_rate(port_base + i, GPIO_SLEW_RATE_FAST), gpio_set_drive_strength(port_base + i, GPIO_DRIVE_STRENGTH_8MA);
    pio_sm_set_consecutive_pindirs(pio, sm, port_base, in_count, false);
    pio_sm_set_consecutive_pindirs(pio, sm, sel_base, 2, true);
    sm_config_set_in_pins(&cfg, port_base);
    sm_config_set_out_pins(&cfg, port_base, 8);
    sm_config_set_sideset_pins(&cfg, sel_base);
    sm_config_set_in_shift(&cfg, false /*shift left*/, false, 32);
    sm_config_set_out_shift(&cfg, true /*shift right*/, false, 32);
    sm_config_set_clkdiv(&cfg, 1.0f);
    pio_sm_init(pio, sm, prog_offset, &cfg);
}

void bus_init(cart_t *c) {
    g_cart = c;
    gpio_init(PIN_CPU_M2); gpio_set_input_hysteresis_enabled(PIN_CPU_M2, true);
    gpio_init(PIN_PPU_ACC); gpio_set_input_hysteresis_enabled(PIN_PPU_ACC, true);
    gpio_init(PIN_IRQ); gpio_put(PIN_IRQ, 1); gpio_set_dir(PIN_IRQ, true);
    gpio_init(PIN_CIRAM_A10); gpio_set_dir(PIN_CIRAM_A10, true);
    gpio_init(PIN_CIRAM_CE); gpio_set_dir(PIN_CIRAM_CE, true); gpio_put(PIN_CIRAM_CE, 1);

    uint off_cpu = pio_add_program(pio_cpu, &fc_cpu_program);
    uint off_ppu = pio_add_program(pio_ppu, &fc_ppu_program);
    sm_cpu = pio_claim_unused_sm(pio_cpu, true);
    sm_ppu = pio_claim_unused_sm(pio_ppu, true);
    port_init(pio_cpu, sm_cpu, off_cpu, &fc_cpu_program, PIN_CPU_PORT_BASE, 8, PIN_CPU_SEL_BASE);
    port_init(pio_ppu, sm_ppu, off_ppu, &fc_ppu_program, PIN_PPU_PORT_BASE, 8, PIN_PPU_SEL_BASE);

    /* PPU on core1 first so CHR is served as soon as the PPU starts fetching */
    multicore_launch_core1(ppu_bus_core1);
    pio_sm_set_enabled(pio_ppu, sm_ppu, true);

    /* CPU bus: highest-priority IRQ on core0 */
    uint irqn = (pio_cpu == pio0) ? PIO0_IRQ_0 : PIO1_IRQ_0;
    pio_set_irq0_source_enabled(pio_cpu, (enum pio_interrupt_source)(pis_sm0_rx_fifo_not_empty + sm_cpu), true);
    irq_set_exclusive_handler(irqn, cpu_bus_isr);
    irq_set_priority(irqn, 0);
    irq_set_enabled(irqn, true);
    pio_sm_set_enabled(pio_cpu, sm_cpu, true);
}
void bus_stop(void) {
    pio_sm_set_enabled(pio_cpu, sm_cpu, false); pio_sm_set_enabled(pio_ppu, sm_ppu, false);
    multicore_reset_core1();
}

#elif FC_BUS_CAPABLE && FC_BUS_DIRECT
/* ================= rev C: RP2350B, console buses wired directly ================= */
_Static_assert(PIN_CPU_M2 == 24, "fc_bus_direct.pio hardcodes 'wait gpio 24' for M2");
_Static_assert(PIN_PPU_ACC == PIN_PPU_PORT_BASE + 14, "fc_bus_direct.pio waits on IN pin 14 = /PPUACC");
static cart_t *g_cart;
static PIO pio_cpu = pio0, pio_ppu = pio1;
static uint sm_cpu = 0, sm_ppu = 0;
#define RSP_NONE      0u
#define RSP_DRIVE(d)  (1u | ((uint32_t)(d) << 1))
#define RSP_CAPTURE   2u

FC_INLINE void irq_pin_set(bool assert_low) {   /* emulated open drain on a 5 V-tolerant pin: drive low, or float */
    if (assert_low) { sio_hw->gpio_clr = 1u << PIN_IRQ; sio_hw->gpio_oe_set = 1u << PIN_IRQ; }
    else sio_hw->gpio_oe_clr = 1u << PIN_IRQ;
}

static void FC_FASTCODE(cpu_bus_isr)(void) {
    cart_t *c = g_cart;
    static uint8_t awaiting_write; static uint16_t waddr;
    while (!pio_sm_is_rx_fifo_empty(pio_cpu, sm_cpu)) {
        uint32_t w = pio_sm_get(pio_cpu, sm_cpu);   /* bits: 0-14 A, 15-22 D, 23 R/W, 24 M2, 25 /ROMSEL */
        if (awaiting_write) {
            awaiting_write = 0;
            cart_cpu_write(c, waddr, (uint8_t)(w >> 15));
            bus_stat_cpu_writes++;
            irq_pin_set(c->irq_line);
            continue;
        }
        bool rw = (w >> 23) & 1, romsel_n = (w >> 25) & 1;
        uint16_t addr = (uint16_t)((w & 0x7FFF) | (romsel_n ? 0 : 0x8000));
        bus_stat_cpu_cycles++;
        if (rw) {
            if (addr >= 0x4020) {
                const uint8_t *p = c->prg_map[addr >> 13];
                if (p) { uint8_t v = p[addr & 0x1FFF]; pio_sm_put(pio_cpu, sm_cpu, RSP_DRIVE(v)); c->open_bus = v; bus_stat_cpu_reads++; }
                else if (c->has_read_hook) { uint8_t v = c->mapper->read(c, addr, c->open_bus); pio_sm_put(pio_cpu, sm_cpu, RSP_DRIVE(v)); c->open_bus = v; bus_stat_cpu_reads++; }
                else pio_sm_put(pio_cpu, sm_cpu, RSP_NONE);
            } else pio_sm_put(pio_cpu, sm_cpu, RSP_NONE);
        } else {
            if (addr >= 0x4020 || (c->mapper->flags & MF_SNOOP_PPU_REGS)) { pio_sm_put(pio_cpu, sm_cpu, RSP_CAPTURE); awaiting_write = 1; waddr = addr; }
            else pio_sm_put(pio_cpu, sm_cpu, RSP_NONE);
        }
        c->cpu_cycles++;
        if (c->has_cpu_cycle_hook) c->mapper->cpu_cycle(c);
        irq_pin_set(c->irq_line);
    }
}

static void FC_FASTCODE(ppu_bus_core1)(void) {
    cart_t *c = g_cart;
    for (;;) {
        uint32_t w = pio_sm_get_blocking(pio_ppu, sm_ppu);   /* bits: 0-7 A0-7, 8-13 A8-13, 14 /PPUACC, 15 /RD */
        uint16_t addr = (uint16_t)(w & 0x3FFF);
        bool rd_n = (w >> 15) & 1;
        if (c->has_ppu_hook) { c->ppu_override = NULL; c->mapper->ppu_addr(c, addr); }
        if (addr < 0x2000) {
            gpio_put(PIN_CIRAM_CE, 1);
            if (!rd_n) { uint8_t v = c->ppu_override ? *c->ppu_override : c->chr_map[addr >> 10][addr & 0x3FF]; pio_sm_put(pio_ppu, sm_ppu, RSP_DRIVE(v)); bus_stat_ppu_reads++; }
            else { pio_sm_put(pio_ppu, sm_ppu, RSP_CAPTURE); uint8_t v = (uint8_t)pio_sm_get_blocking(pio_ppu, sm_ppu);
                   if (c->chr_wmask & (1u << (addr >> 10))) c->chr_map[addr >> 10][addr & 0x3FF] = v;
                   bus_stat_ppu_writes++; }
        } else if (addr < 0x3F00) {
            unsigned nt = (addr >> 10) & 3; uint8_t *p = c->nt_map[nt];
            if (!p) {
                gpio_put(PIN_CIRAM_A10, c->nt_ciram_a10[nt]);
                gpio_put(PIN_CIRAM_CE, 0);
                if (!rd_n && c->ppu_override) { pio_sm_put(pio_ppu, sm_ppu, RSP_DRIVE(*c->ppu_override)); gpio_put(PIN_CIRAM_CE, 1); }
                else pio_sm_put(pio_ppu, sm_ppu, RSP_NONE);
            } else {
                gpio_put(PIN_CIRAM_CE, 1);
                if (!rd_n) pio_sm_put(pio_ppu, sm_ppu, RSP_DRIVE(c->ppu_override ? *c->ppu_override : p[addr & 0x3FF]));
                else { pio_sm_put(pio_ppu, sm_ppu, RSP_CAPTURE); p[addr & 0x3FF] = (uint8_t)pio_sm_get_blocking(pio_ppu, sm_ppu); }
            }
        } else { gpio_put(PIN_CIRAM_CE, 1); pio_sm_put(pio_ppu, sm_ppu, RSP_NONE); }
    }
}

void bus_init(cart_t *c) {
    g_cart = c;
    for (uint g = PIN_CPU_BASE; g < PIN_CPU_BASE + 26; g++) { pio_gpio_init(pio_cpu, g); gpio_set_input_hysteresis_enabled(g, true); gpio_set_slew_rate(g, GPIO_SLEW_RATE_FAST); }
    gpio_init(PIN_IRQ); gpio_put(PIN_IRQ, 0); gpio_set_dir(PIN_IRQ, false);
    gpio_init(PIN_CIRAM_A10); gpio_set_dir(PIN_CIRAM_A10, true);
    gpio_init(PIN_CIRAM_CE); gpio_set_dir(PIN_CIRAM_CE, true); gpio_put(PIN_CIRAM_CE, 1);

    /* CPU: PIO0, GPIO window 0..31 */
    uint off_cpu = pio_add_program(pio_cpu, &fc_cpu_direct_program);
    sm_cpu = pio_claim_unused_sm(pio_cpu, true);
    pio_sm_config cfg = fc_cpu_direct_program_get_default_config(off_cpu);
    sm_config_set_in_pins(&cfg, PIN_CPU_BASE);
    sm_config_set_out_pins(&cfg, PIN_CPU_DATA_BASE, 8);
    sm_config_set_in_shift(&cfg, false, false, 32);
    sm_config_set_out_shift(&cfg, true, false, 32);
    pio_sm_set_consecutive_pindirs(pio_cpu, sm_cpu, PIN_CPU_BASE, 26, false);
    pio_sm_init(pio_cpu, sm_cpu, off_cpu, &cfg);

    /* PPU: PIO1, GPIO window 16..47 */
    pio_set_gpio_base(pio_ppu, 16);
    for (uint g = PIN_PPU_PORT_BASE; g <= PIN_PPU_SEL; g++) { pio_gpio_init(pio_ppu, g); gpio_set_input_hysteresis_enabled(g, true); gpio_set_slew_rate(g, GPIO_SLEW_RATE_FAST); }
    uint off_ppu = pio_add_program(pio_ppu, &fc_ppu_direct_program);
    sm_ppu = pio_claim_unused_sm(pio_ppu, true);
    pio_sm_config pcfg = fc_ppu_direct_program_get_default_config(off_ppu);
    sm_config_set_in_pins(&pcfg, PIN_PPU_PORT_BASE);
    sm_config_set_out_pins(&pcfg, PIN_PPU_PORT_BASE, 8);
    sm_config_set_sideset_pins(&pcfg, PIN_PPU_SEL);
    sm_config_set_in_shift(&pcfg, false, false, 32);
    sm_config_set_out_shift(&pcfg, true, false, 32);
    pio_sm_set_consecutive_pindirs(pio_ppu, sm_ppu, PIN_PPU_PORT_BASE, 16, false);
    pio_sm_set_consecutive_pindirs(pio_ppu, sm_ppu, PIN_PPU_SEL, 1, true);
    pio_sm_init(pio_ppu, sm_ppu, off_ppu, &pcfg);

    multicore_launch_core1(ppu_bus_core1);
    pio_sm_set_enabled(pio_ppu, sm_ppu, true);
    uint irqn = PIO0_IRQ_0;
    pio_set_irq0_source_enabled(pio_cpu, (enum pio_interrupt_source)(pis_sm0_rx_fifo_not_empty + sm_cpu), true);
    irq_set_exclusive_handler(irqn, cpu_bus_isr); irq_set_priority(irqn, 0); irq_set_enabled(irqn, true);
    pio_sm_set_enabled(pio_cpu, sm_cpu, true);
}
void bus_stop(void) { pio_sm_set_enabled(pio_cpu, sm_cpu, false); pio_sm_set_enabled(pio_ppu, sm_ppu, false); multicore_reset_core1(); }
#else
void bus_init(cart_t *c) { (void)c; }
void bus_stop(void) {}
#endif
