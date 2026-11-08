/* famicart rev E inter-MCU link: one shared 3.3 V line between U1 (CPU-side Pico 2, master), U2 (PPU-side Pico 2)
 * and U3 (XIAO RP2350, IRQ + expansion audio). Half duplex, asynchronous 12-bit symbols: start bit, 10 data bits,
 * stop bit. Data bit 9 marks the first symbol of a frame, so a receiver that loses a symbol re-aligns on the next
 * frame. Only U1 starts frames; U2/U3 answer a POLL with exactly one reply symbol (bit 9 = 0).
 *
 * Frames (S = start symbol, d = data symbol, low 9 bits shown):
 *   CPU write      S:0 A15..A8   d:A7..A0  d:D           (3 symbols; every write >= $4020, $2000/$2001 for MMC5)
 *   SEQ write      S:1 00        d:D                     (write to previous write address + 1: ExRAM / RAM fills)
 *   PPU address    S:1 01        d:inc32<<6 | A13..A8    d:A7..A0   (VRAM pointer for the following PPU data)
 *   PPU data       S:1 02        d:D                     (store at the VRAM pointer, then pointer += 1 or 32)
 *   CPU read       S:1 03        d:A15..A8  d:A7..A0     (read with side effects: MMC5 $5204, N163 $4800 ...)
 *   POLL           S:1 04        d:node                  (node answers one symbol: its status byte)
 *   LOAD           S:1 05        d:len lo   d:len hi  d * len   (cart description blob, see reve_load_t)
 *   BULK address   S:1 06        d:a7..0  d:a15..8  d:a23..16    (CHR byte offset for the following BULK data)
 *   BULK data      S:1 07        d:n-1  d * n            (n <= 256 CHR bytes, offset advances)
 *   COMMAND        S:1 08        d:sub   d:arg
 * This file is portable (host tests use the same encoder/decoder as the firmware). */
#pragma once
#include <stdint.h>
#include <stdbool.h>

#define RL_START          0x200u
#define RL_CMD            0x100u
#define RL_SEQ_W          0x00u
#define RL_PPU_ADDR       0x01u
#define RL_PPU_DATA       0x02u
#define RL_CPU_READ       0x03u
#define RL_POLL           0x04u
#define RL_LOAD           0x05u
#define RL_BULK_ADDR      0x06u
#define RL_BULK           0x07u
#define RL_COMMAND        0x08u

/* COMMAND sub-codes */
#define RL_C_RESET        1u    /* back to the idle state (no game) */
#define RL_C_LIVE         2u    /* arg 1: game tables live (start serving), 0: idle */
#define RL_C_LED          3u
#define RL_C_CHR_COMMIT   4u    /* U2: all CHR received; arg 1 = store in flash (CHR larger than SRAM) */
#define RL_C_CHR_QUERY    5u    /* U2: next POLL answers 1 when the CHR with the CRC in the last LOAD is already cached */

#define RL_NODE_PPU       2u
#define RL_NODE_X         3u
#define RL_NODE_COP_CPU   4u    /* rev F U4 */
#define RL_NODE_COP_PPU   5u    /* rev F U5: status byte bit7 = busy */

/* Status bytes returned to a POLL */
#define RL_ST_BUSY        0x00u
#define RL_ST_READY       0x01u    /* | flags */
#define RL_ST_ERROR       0xEEu
#define RL_ST_MMC5_IRQ    0x80u    /* U3: MMC5 IRQ pending */
#define RL_ST_MMC5_FRAME  0x40u    /* U3: MMC5 in frame */
#define RL_ST_VALID       0x20u    /* U3: status byte carries MMC5 bits */

/* ---- encoder: writes symbols into out[], returns the count ---- */
static inline unsigned rl_enc_write(uint16_t *o, uint16_t a, uint8_t d) { o[0] = (uint16_t)(RL_START | (a >> 8)); o[1] = a & 0xFF; o[2] = d; return 3; }
static inline unsigned rl_enc_seq(uint16_t *o, uint8_t d) { o[0] = RL_START | RL_CMD | RL_SEQ_W; o[1] = d; return 2; }
static inline unsigned rl_enc_ppu_addr(uint16_t *o, uint16_t a, bool inc32) { o[0] = RL_START | RL_CMD | RL_PPU_ADDR; o[1] = (uint16_t)(((a >> 8) & 0x3F) | (inc32 ? 0x40 : 0)); o[2] = a & 0xFF; return 3; }
static inline unsigned rl_enc_ppu_data(uint16_t *o, uint8_t d) { o[0] = RL_START | RL_CMD | RL_PPU_DATA; o[1] = d; return 2; }
static inline unsigned rl_enc_read(uint16_t *o, uint16_t a) { o[0] = RL_START | RL_CMD | RL_CPU_READ; o[1] = a >> 8; o[2] = a & 0xFF; return 3; }
static inline unsigned rl_enc_poll(uint16_t *o, uint8_t node) { o[0] = RL_START | RL_CMD | RL_POLL; o[1] = node; return 2; }
static inline unsigned rl_enc_cmd(uint16_t *o, uint8_t sub, uint8_t arg) { o[0] = RL_START | RL_CMD | RL_COMMAND; o[1] = sub; o[2] = arg; return 3; }
static inline unsigned rl_enc_bulk_addr(uint16_t *o, uint32_t off) { o[0] = RL_START | RL_CMD | RL_BULK_ADDR; o[1] = off & 0xFF; o[2] = (off >> 8) & 0xFF; o[3] = (off >> 16) & 0xFF; return 4; }
static inline unsigned rl_enc_bulk(uint16_t *o, const uint8_t *p, unsigned n) { o[0] = RL_START | RL_CMD | RL_BULK; o[1] = (uint16_t)(n - 1); for (unsigned i = 0; i < n; i++) o[2 + i] = p[i]; return 2 + n; }
static inline unsigned rl_enc_load_head(uint16_t *o, unsigned len) { o[0] = RL_START | RL_CMD | RL_LOAD; o[1] = len & 0xFF; o[2] = (len >> 8) & 0xFF; return 3; }

/* ---- decoder ---- */
typedef enum { RL_EV_NONE = 0, RL_EV_WRITE, RL_EV_PPU_ADDR, RL_EV_PPU_DATA, RL_EV_READ, RL_EV_POLL, RL_EV_LOAD, RL_EV_BULK_ADDR, RL_EV_BULK_BYTE, RL_EV_COMMAND, RL_EV_BAD } rl_ev_kind_t;
typedef struct { rl_ev_kind_t kind; uint16_t addr; uint8_t data, arg; uint32_t off; } rl_event_t;

#define RL_LOAD_MAX 192
typedef struct {
    uint8_t  type, need, have; uint16_t sym0;
    uint8_t  b[4];
    uint16_t last_waddr;
    uint16_t load_len, load_fill; uint8_t load[RL_LOAD_MAX];
    uint16_t bulk_left; uint32_t bulk_off;
    uint32_t bad;
} rl_dec_t;

void rl_dec_init(rl_dec_t *d);
/* Feed one received symbol. Returns true and fills *ev when an event is complete (LOAD: ev->kind = RL_EV_LOAD
 * once the whole blob is in d->load[]; BULK: one RL_EV_BULK_BYTE event per byte, off = its CHR offset). */
bool rl_dec_feed(rl_dec_t *d, uint16_t sym, rl_event_t *ev);

/* Cart description sent with LOAD: everything U2/U3 need to build the same mapper state as U1. */
typedef struct {
    uint16_t mapper; uint8_t submapper, mirroring;
    uint8_t  battery, system, has_profile, flags;    /* flags bit0: CHR is RAM, bit1: forward PPU data */
    uint32_t prg_size, chr_size, chr_ram_size, wram_size, sram_size;
    uint32_t chr_crc;                                 /* CRC32 of the CHR data (U2 flash cache key) */
    uint8_t  profile[64];                             /* cart_profile_t when has_profile */
} reve_load_t;
_Static_assert(sizeof(reve_load_t) <= RL_LOAD_MAX, "reve_load_t too big for the LOAD frame");
