/* rev D, U1: drive the local CPU bus while the console side is isolated: program/read the PRG flash (S29GL01GS,
 * x16 device used on DQ0-7), access the F-RAM, and program/read the CHR flash through U2 and the data bridge. */
#pragma once
#include <stdint.h>
#include <stdbool.h>
void nor_bus_take(void);                       /* ISOLATE=1, stop the snoop, take over the local bus */
void nor_bus_release(void);                    /* back to run mode (caller restarts the front-end) */
uint8_t nor_prg_read(uint32_t addr);           /* 26-bit byte address */
bool nor_prg_erase_sector(uint32_t addr);      /* 128 KB sector containing addr */
bool nor_prg_program(uint32_t addr, const uint8_t *data, uint32_t len);   /* write-buffer programming, any alignment */
uint16_t nor_prg_id(uint8_t *mfr);             /* device id (0x227E for GL family) */
void nor_wram_write(uint32_t addr, uint8_t v);
uint8_t nor_wram_read(uint32_t addr);
/* CHR flash via U2 (link must be up; U2 in programming mode) */
bool nor_chr_erase_sector(uint32_t addr);
bool nor_chr_program(uint32_t addr, const uint8_t *data, uint32_t len);
uint8_t nor_chr_read(uint32_t addr);
bool nor_chr_begin(void);                      /* put U2 into programming mode */
void nor_chr_end(void);
