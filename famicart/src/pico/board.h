/* Board selection. Every pin number used by bus.c / audio_out.c / audio_link.c comes from here. */
#pragma once
#if defined(FC_BOARD_xiao_rp2040)
#include "board_xiao_rp2040.h"      /* XIAO alone: no bus (bench/self-test build) */
#elif defined(FC_BOARD_xiao_audio)
#include "board_xiao_audio.h"       /* rev C coprocessor: audio synth fed over UART */
#elif defined(FC_BOARD_rp2350b)
#include "board_rp2350b.h"          /* rev C main MCU */
#elif defined(FC_BOARD_revd_prg)
#include "board_revd_prg.h"         /* rev D U1: PRG mapper / expansion chip */
#elif defined(FC_BOARD_revd_chr)
#include "board_revd_chr.h"         /* rev D U2: CHR mapper */
#else
#include "board_pico.h"             /* rev A/B: Pico / Pico 2 module, buffered buses */
#endif
#ifndef FC_BUS_DIRECT
#define FC_BUS_DIRECT 0
#endif
#ifndef FC_AUDIO_REMOTE
#define FC_AUDIO_REMOTE 0
#endif
#ifndef FC_AUDIO_COPROCESSOR
#define FC_AUDIO_COPROCESSOR 0
#endif
#ifndef FC_BUS_REVD
#define FC_BUS_REVD 0
#endif
#ifndef FC_VIRTUAL_ROM
#define FC_VIRTUAL_ROM 0
#endif
