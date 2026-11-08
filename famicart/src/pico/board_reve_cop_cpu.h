/* famicart rev F, U4: Raspberry Pi Pico 2, CPU-side coprocessor. Same pin map as U1 (shares A0-14, /ROMSEL, /WS
 * behind U1's resistors; D0-D7 through its own 1k array). Answers only its window (docs/09_coproc_abi.md). */
#pragma once
#include "board_reve_cpu.h"
#define FC_COP_CPU 1
