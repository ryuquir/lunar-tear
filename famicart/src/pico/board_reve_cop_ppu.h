/* famicart rev F, U5: Raspberry Pi Pico 2, PPU-side coprocessor. Same pin map as U2 for PA0-13, PD0-7, /RD
 * (PD through its own 1k array); GP26/27 unconnected (U2 drives CIRAM). Serves only the CHR slots it owns. */
#pragma once
#include "board_reve_ppu.h"
#define FC_COP_PPU 1
