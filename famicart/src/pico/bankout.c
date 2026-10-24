#include "bankout.h"
#include "board.h"
#include "../core/cartload.h"
#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include "hardware/structs/sio.h"
#include "hardware/sync.h"

/* GPIO27-31 carry bank bits 0-4 (gpio_out), GPIO32-39 bits 5-12 and GPIO40 = WRAM_nCE (gpio_hi_out). */
#define LO_SHIFT   (PIN_PRG_BANK_BASE)                /* 27 */
#define LO_MASK    (0x1Fu << LO_SHIFT)
#define HI_MASK    (0x1FFu)                           /* GPIO32..40 */
#define HI_WRAM    (1u << (PIN_WRAM_NCE - 32))

static volatile uint32_t word_lo[8], word_hi[8];    /* indexed by CPU address >> 13 (0..7) */
static volatile bool live;
static uint32_t base_bank;

static inline void encode(uint32_t bank, bool wram, uint32_t *lo, uint32_t *hi) {
    bank &= 0x1FFF;
    *lo = (bank & 0x1F) << LO_SHIFT;
    *hi = ((bank >> 5) & 0xFF) | (wram ? 0 : HI_WRAM);
}
void bankout_init(void) {
    for (uint g = PIN_PRG_BANK_BASE; g < PIN_PRG_BANK_BASE + PIN_PRG_BANK_BITS; g++) { gpio_init(g); gpio_set_dir(g, true); gpio_put(g, 1); gpio_set_slew_rate(g, GPIO_SLEW_RATE_FAST); }
    gpio_init(PIN_WRAM_NCE); gpio_set_dir(PIN_WRAM_NCE, true); gpio_put(PIN_WRAM_NCE, 1);
    bankout_boot();
}
void bankout_boot(void) {
    for (int i = 0; i < 8; i++) { uint32_t lo, hi; encode(FC_BOOT_BANK, false, &lo, &hi); word_lo[i] = lo; word_hi[i] = hi; }
    live = false;
}
void bankout_set_cart(cart_t *c, uint32_t prg_base_bank) { base_bank = prg_base_bank; bankout_update(c); }
void bankout_update(cart_t *c) {
    c->tables_dirty = 0;
    uint32_t lo[8], hi[8];
    for (int i = 0; i < 8; i++) {
        bool wram = false; uint32_t bank = FC_BOOT_BANK;
        const uint8_t *p = c->prg_map[i];
        if (i >= 4) {
            if (p && (uintptr_t)p >= FC_VROM_PRG && (uintptr_t)p < FC_VROM_PRG + 0x4000000u) bank = base_bank + (((uintptr_t)p - FC_VROM_PRG) >> 13);
            else if (p && (uintptr_t)p >= FC_VROM_WRAM && (uintptr_t)p < FC_VROM_WRAM + FC_VROM_WRAM_SIZE) { wram = true; bank = ((uintptr_t)p - FC_VROM_WRAM) >> 13; }
        } else if (i == 3) {
            if (p && (uintptr_t)p >= FC_VROM_WRAM && (uintptr_t)p < FC_VROM_WRAM + FC_VROM_WRAM_SIZE) { wram = true; bank = ((uintptr_t)p - FC_VROM_WRAM) >> 13; }
            /* PRG-ROM at $6000 cannot be served by the flash (/CE follows /ROMSEL): left unmapped (see docs) */
        }
        encode(bank, wram, &lo[i], &hi[i]);
    }
    uint32_t s = save_and_disable_interrupts();
    for (int i = 0; i < 8; i++) { word_lo[i] = lo[i]; word_hi[i] = hi[i]; }
    restore_interrupts(s);
}
void bankout_go(bool l) { live = l; }
void bankout_set_raw(uint32_t bank, bool wram_sel) {
    uint32_t lo, hi; encode(bank, wram_sel, &lo, &hi);
    sio_hw->gpio_togl = (sio_hw->gpio_out ^ lo) & LO_MASK;
    sio_hw->gpio_hi_togl = (sio_hw->gpio_hi_out ^ hi) & HI_MASK;
}

/* Core 1: watch CA13/CA14/CnROMSEL and put the window's bank on the lines. ~60 ns at 150 MHz. */
void __not_in_flash_func(bankout_core1)(void) {
    uint32_t last = 0xFF;
    uint32_t cur_lo = sio_hw->gpio_out & LO_MASK, cur_hi = sio_hw->gpio_hi_out & HI_MASK;
    for (;;) {
        uint32_t in = sio_hw->gpio_in;
        uint32_t idx = ((in >> 13) & 3) | (((in >> PIN_CPU_ROMSEL) & 1) ? 0 : 4);
        if (idx != last) {
            last = idx;
            uint32_t lo = word_lo[idx], hi = word_hi[idx];
            if (lo != cur_lo) { sio_hw->gpio_togl = (lo ^ cur_lo); cur_lo = lo; }
            if (hi != cur_hi) { sio_hw->gpio_hi_togl = (hi ^ cur_hi); cur_hi = hi; }
        }
    }
}
