/* famicart coprocessor ABI v1 (rev F, docs/09_coproc_abi.md). Portable.
 *
 * CPU window $5800-$5BFF (base relocatable via the cart profile):
 *   $5800        CMD      write = start a command (STATUS.busy = 1 until done)
 *   $5801        STATUS   bit7 busy, bit6 error, bits 3-0 = ABI version
 *   $5802-$580F  ARG/RES  arguments in, results out (little endian)
 *   $5810-$5BEF  SRAM     shared RAM, readable/writable by the CPU at any time (992 bytes)
 *   $5BF0-$5BFE  PPU command block (write only, forwarded to the PPU coprocessor): $5BF0 = CMD, $5BF1-$5BFE = args
 *   $5BFF        PPU STATUS (read): bit7 busy
 * U4 answers $5800-$5BEF; U1 answers $5BFF (from POLLs of U5); nobody drives $5BF0-$5BFE.
 * The PPU coprocessor owns the CHR 1 KB slots given by the profile (coproc_chr_mask) and draws into them. */
#pragma once
#include <stdint.h>
#include <stdbool.h>

#define COP_ABI_VERSION   1
#define COP_BASE_DEFAULT  0x5800u
#define COP_WIN_SIZE      0x400u
#define COP_R_CMD         0x000u
#define COP_R_STATUS      0x001u
#define COP_R_ARG         0x002u      /* 14 bytes */
#define COP_R_SRAM        0x010u
#define COP_SRAM_SIZE     (0x3F0u - 0x010u)
#define COP_R_PPU_CMD     0x3F0u
#define COP_R_PPU_ARG     0x3F1u      /* 14 bytes */
#define COP_R_PPU_STATUS  0x3FFu
#define COP_ST_BUSY       0x80u
#define COP_ST_ERROR      0x40u

/* CPU-side commands (U4). Arguments at ARG+0.. */
#define COP_C_NOP         0x00u
#define COP_C_MUL16       0x01u   /* a16 (ARG0-1) * b16 (ARG2-3) -> u32 (ARG4-7); ARG8 bit0 = signed */
#define COP_C_DIV32       0x02u   /* u32 (ARG0-3) / u16 (ARG4-5) -> q32 (ARG6-9), r16 (ARG10-11); /0 -> error */
#define COP_C_MEMSET      0x03u   /* SRAM[off16 ARG0-1 .. +len16 ARG2-3] = ARG4 */
#define COP_C_MEMCPY      0x04u   /* SRAM dst16 ARG0-1 <- src16 ARG2-3, len16 ARG4-5 (overlap safe) */
#define COP_C_SINCOS      0x05u   /* angle8 ARG0 (256 = full turn) -> sin16 ARG2-3, cos16 ARG4-5 (s1.14 fixed point) */
#define COP_C_ROT2D       0x06u   /* (x16 ARG0-1, y16 ARG2-3) rotated by angle8 ARG4 -> x16 ARG6-7, y16 ARG8-9 (signed) */

/* PPU-side commands (U5), drawing into the owned CHR area as a 128 x 128 px, 2 bpp bitmap per buffer:
 * 16 x 16 tiles, tile n at n * 16 (NES planar format). Buffer 0 = owned CHR bytes $0000-$0FFF of the area,
 * buffer 1 = $1000-$1FFF (when 8 slots are owned). The CPU points BG tiles at it once and then just draws. */
#define COP_P_CLEAR       0x01u   /* color ARG0 (0-3) */
#define COP_P_PLOT        0x02u   /* x ARG0, y ARG1, color ARG2 */
#define COP_P_LINE        0x03u   /* x0 ARG0, y0 ARG1, x1 ARG2, y1 ARG3, color ARG4 */
#define COP_P_RECT        0x04u   /* x ARG0, y ARG1, w ARG2, h ARG3, color ARG4 (filled) */
#define COP_P_SELECT      0x05u   /* draw buffer ARG0 (0/1) */
