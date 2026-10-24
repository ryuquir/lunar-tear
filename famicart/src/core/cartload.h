/* Build a cart_t from a ROM image + rom_info + profile, using static SRAM pools. */
#pragma once
#include "cart.h"
#include "rom.h"
#include "profile.h"

#ifndef FC_ROM_POOL_SIZE
#define FC_ROM_POOL_SIZE (200 * 1024)   /* PRG+CHR copy; board files override */
#endif
#ifndef FC_RAM_POOL_SIZE
#define FC_RAM_POOL_SIZE (44 * 1024)    /* WRAM (<=32K) + CHR-RAM/ExRAM/ext VRAM */
#endif

typedef enum { LOAD_OK = 0, LOAD_ERR_INSPECT, LOAD_ERR_TOO_BIG, LOAD_ERR_MAPPER, LOAD_ERR_RAM } load_result_t;

/* `img` may live in flash (XIP); PRG/CHR are copied into SRAM. `profile` may be NULL. */
load_result_t cart_load(cart_t *c, const uint8_t *img, uint32_t len, const cart_profile_t *profile, rom_info_t *info_out);
load_result_t cart_load_from_info(cart_t *c, const uint8_t *img, const rom_info_t *info, const cart_profile_t *profile);

/* FC_VIRTUAL_ROM (rev D): table pointers are virtual addresses into external memories. */
#ifndef FC_VIRTUAL_ROM
#define FC_VIRTUAL_ROM 0
#endif
#define FC_VROM_PRG         0x60000000u   /* PRG flash  (64 MB window)  */
#define FC_VROM_CHR         0x68000000u   /* CHR flash  (64 MB window)  */
#define FC_VROM_CHRRAM      0x70000000u   /* CHR SRAM   (512 KB)        */
#define FC_VROM_CHRRAM_SIZE 0x80000u
#define FC_VROM_WRAM        0x78000000u   /* F-RAM      (128 KB)        */
#define FC_VROM_WRAM_SIZE   0x20000u
const char *cart_load_strerror(load_result_t r);
uint32_t cart_rom_pool_size(void);
