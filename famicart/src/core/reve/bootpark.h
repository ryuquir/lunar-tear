/* rev E boot handshake. While no game is live U1 answers every $8000-$FFFF read with $4C, so the CPU -- at power-on,
 * after RESET, or in the middle of a game being replaced -- lands in "JMP $4C4C" at $4C4C within one instruction
 * once U1 runs (before that the bus is undefined: the pad pull-downs of an RP2350 in reset outweigh any weak pull, so
 * a CPU that started first may need the console's RESET button). NMI/IRQ vectors also read $4C4C, so an enabled NMI
 * just re-enters the loop.
 * To start a game U1 arms the handshake: the next opcode fetch at $4C4C gets $6C and the operand reads $FC $FF,
 * i.e. JMP ($FFFC); the two vector reads that follow come from the game's tables, and the CPU starts the game
 * exactly as after power-on. Any break in the sequence just falls back into the loop.
 * The handshake only advances when the $6C really went out: core 0 may arm while the CPU is in the middle of the
 * opcode fetch that was already answered with $4C, and operands $FC $FF after that opcode would be JMP $FFFC. */
#pragma once
#include <stdint.h>
#include <stdbool.h>

typedef enum { BP_PARKED = 0, BP_ARMED, BP_JUMP, BP_RUN } bp_state_t;
typedef struct { volatile uint8_t state; uint8_t step; uint8_t saw_fffd; uint8_t served; } bootpark_t;

static inline void bootpark_init(bootpark_t *b) { b->state = BP_PARKED; b->step = 0; b->saw_fffd = 0; b->served = 0; }
static inline void bootpark_arm(bootpark_t *b) { b->step = 0; b->saw_fffd = 0; b->served = 0; b->state = BP_ARMED; }
static inline void bootpark_park(bootpark_t *b) { b->state = BP_PARKED; b->step = 0; b->served = 0; }

/* Byte for a $4020-$7FFF address while not running. Returns false when U1 should not drive. */
static inline bool bootpark_low(bootpark_t *b, uint16_t a, uint8_t *v) {
    if (a < 0x4C4C || a > 0x4C4E) return false;
    if (b->state == BP_ARMED) {
        static const uint8_t seq[3] = { 0x6C, 0xFC, 0xFF };
        unsigned i = a - 0x4C4C;
        *v = (i == b->step) ? seq[i] : 0x4C;               /* operands only right after our own opcode */
        if (i == 0 && b->step == 0) b->served = 1;         /* this opcode fetch is being answered with $6C */
        return true;
    }
    if (b->state == BP_PARKED) { *v = 0x4C; return true; }
    return false;
}
/* ROM ($8000-$FFFF) byte while not running: game byte for the reset vector during the jump, else $4C. */
static inline uint8_t bootpark_rom(bootpark_t *b, uint16_t a, uint8_t game) {
    if (b->state == BP_JUMP) {
        if (a == 0xFFFC) return game;
        if (a == 0xFFFD) { b->saw_fffd = 1; return game; }
        if (b->saw_fffd) { b->state = BP_RUN; return game; }   /* first fetch of the game's reset code */
    }
    return 0x4C;
}
/* Confirmed read (rcommit) of the handshake addresses. */
static inline void bootpark_commit(bootpark_t *b, uint16_t a) {
    if (b->state != BP_ARMED) return;
    if (a == 0x4C4C) { b->step = b->served ? 1 : 0; b->served = 0; }
    else if (a == 0x4C4D && b->step == 1) b->step = 2;
    else if (a == 0x4C4E && b->step == 2) { b->step = 0; b->state = BP_JUMP; }
    else b->step = 0;
}
