/* Per-mapper state structs. One union member per mapper family. */
#pragma once
#include <stdint.h>
#include <stdbool.h>

typedef struct { uint8_t shift, count, ctrl, chr0, chr1, prg; uint8_t last_cycle_write; uint32_t last_write_cycle; } mmc1_state_t;

typedef struct {
    uint8_t bank_select, regs[8], prg_mode, chr_mode;
    uint8_t irq_latch, irq_counter, irq_enable, irq_reload;
    uint8_t wram_ctrl, mirroring;
    uint32_t last_a12_cycle; uint8_t a12_state;
    uint8_t variant;   /* 0 MMC3, 1 MMC6, 2 TxSROM(118), 3 TQROM(119), 4 MC-ACC, 5 Namcot108 family */
} mmc3_state_t;

typedef struct {
    uint8_t prg_mode, chr_mode, exram_mode, nt_map, fill_tile, fill_color;
    uint8_t prg_bank[5], prg_ram_protect1, prg_ram_protect2;
    uint16_t chr_bank_a[8], chr_bank_b[4];
    uint8_t chr_upper, last_chr_set;
    uint8_t mult_a, mult_b;
    uint8_t irq_scanline_cmp, irq_enable, irq_pending, in_frame;
    uint8_t scanline, spr8x16;
    uint8_t split_ctrl, split_scroll, split_bank;
    uint32_t last_ppu_cycle; uint16_t last_ppu_addr; uint8_t match_count, ppu_idle;
    /* audio: regs $5000-$5015 are forwarded to audio/mmc5_audio via the register router */
} mmc5_state_t;

typedef struct { uint8_t latch0, latch1; uint8_t chr_fd0, chr_fe0, chr_fd1, chr_fe1; } mmc2_state_t;

typedef struct {
    uint8_t prg[2], chr[8], swap_mode, wram_en, mirroring;
    uint8_t irq_latch, irq_ctrl, irq_enabled_after_ack; uint8_t irq_counter; int16_t prescaler;
} vrc4_state_t;

typedef struct { uint8_t prg16, prg8, chr[8], ctrl; uint8_t irq_latch, irq_ctrl, irq_counter; int16_t prescaler; } vrc6_state_t;
typedef struct { uint8_t prg[3], chr[8], mirroring; uint8_t irq_latch, irq_ctrl, irq_counter; int16_t prescaler; } vrc7_state_t;

typedef struct { uint8_t cmd, prg[4], chr[8], wram_en, wram_bank; uint16_t irq_counter, irq_reload; uint8_t irq_enable; } fme7_state_t;

typedef struct {
    uint8_t prg[3], chr[8], nt[4], ram_addr, ram_inc, ram_wren, chr_ram_lo, chr_ram_hi;
    uint16_t irq_counter; bool irq_enable;
} n163_state_t;

typedef struct { uint8_t regs[16], prg, mirroring; uint16_t irq_counter; bool irq_enable; uint8_t eeprom_sda, eeprom_scl, eeprom_out; uint8_t eeprom_mode, eeprom_bits, eeprom_addr, eeprom_data; uint8_t eeprom_mem[256]; } bandai_state_t;

typedef struct { uint8_t prg[3], chr[8], mirroring; uint16_t irq_counter, irq_reload; uint8_t irq_enable, irq_mode; } jaleco_state_t;

typedef struct { uint8_t prg[2], chr[6], mirroring, wram_en; uint8_t irq_latch, irq_counter, irq_enable, irq_reload; } taito_state_t;

typedef struct { uint8_t bank, prg_mode, mirroring, chr[8], prg[3]; uint8_t irq_latch, irq_counter, irq_enable, irq_reload, irq_mode; uint8_t irq_delay; uint8_t a12_state; } rambo1_state_t;

typedef struct { uint8_t regs[32]; uint16_t r16[8]; uint32_t r32[4]; bool b[8]; } generic_state_t;

typedef union {
    mmc1_state_t    mmc1;
    mmc3_state_t    mmc3;
    mmc5_state_t    mmc5;
    mmc2_state_t    mmc2;
    vrc4_state_t    vrc4;
    vrc6_state_t    vrc6;
    vrc7_state_t    vrc7;
    fme7_state_t    fme7;
    n163_state_t    n163;
    bandai_state_t  bandai;
    jaleco_state_t  jaleco;
    taito_state_t   taito;
    rambo1_state_t  rambo1;
    generic_state_t g;
    uint8_t         raw[512];
} mapper_state_t;
