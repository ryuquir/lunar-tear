/* rev D inter-MCU link: U1 -> U2 32-bit frames over CLK/DATA (PIO), U2 -> U1 bytes over a PIO UART. */
#pragma once
#include <stdint.h>
#include <stdbool.h>
#include "board.h"

#define LINK_TAG            0xAu
#define LINK_T_SYNC         0x0   /* payload 0 */
#define LINK_T_CPU_WRITE    0x1   /* payload: addr16 << 8 | data8 */
#define LINK_T_CPU_READ     0x2   /* payload: addr16 (read side effects only, e.g. MMC5 $5204) */
#define LINK_T_LOAD_BEGIN   0x3   /* payload: total bytes of the blob that follows (rom_info + profile + bases) */
#define LINK_T_LOAD_DATA    0x4   /* payload: 3 bytes */
#define LINK_T_LOAD_END     0x5   /* payload 0: U2 builds its cart and replies 'L' */
#define LINK_T_CMD          0x6   /* payload: sub-command (LINK_C_*) << 16 | arg16 */
#define LINK_T_CHR_ADDR     0x7   /* payload: CHR flash/RAM byte address bits 23..0 */
#define LINK_T_CHR_ADDR_HI  0x8   /* payload: address bits 25..24 (bit 2 = 1 selects CHR RAM instead of flash) */
#define LINK_T_CHR_WRITE    0x9   /* payload 0: pulse /WE with U1's data on the bridge; U2 replies 'K' */
#define LINK_T_CHR_READ     0xA   /* payload 0: bridge reversed, /OE asserted until CHR_READ_END; replies 'K' when the bus is set up */
#define LINK_T_CHR_READ_END 0xB

#define LINK_C_RESET        1     /* U2: back to boot state, outputs idle */
#define LINK_C_ISOLATE      2     /* arg: 1 = programming mode (U2 drives PA/PnRD/PnWR, bridge enabled), 0 = run */
#define LINK_C_BOOT         3     /* arg: 1 = enter game (tables live), 0 = boot bank state */
#define LINK_C_LED          4

/* U2 -> U1 bytes */
#define LINK_R_ACK          'K'
#define LINK_R_LOADED       'L'
#define LINK_R_ERROR        'E'
#define LINK_R_MMC5_STATUS  0x80  /* | in_frame << 6 | irq_pending << 7 ... low bits: status */
#define LINK_R_RYBY         0x40  /* | ready */

static inline uint32_t link_frame(unsigned type, uint32_t payload) { return (LINK_TAG << 28) | ((type & 0xF) << 24) | (payload & 0xFFFFFFu); }

#if FC_ROLE_PRG
void maplink_init(void);
void maplink_send(uint32_t frame);                       /* non-blocking when the FIFO has room, else spins */
bool maplink_send_try(uint32_t frame);                   /* ISR-safe: false when the FIFO is full */
int  maplink_recv_byte(uint32_t timeout_us);             /* -1 on timeout */
bool maplink_wait_ack(int expect, uint32_t timeout_us);
#endif
#if FC_ROLE_CHR
void maplink_init(void);
bool maplink_poll(uint32_t *frame);                      /* returns one validated frame */
void maplink_reply(uint8_t b);
#endif
