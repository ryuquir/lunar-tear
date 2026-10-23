/* Board selection. Every pin number used by bus.c / audio_out.c comes from here. */
#pragma once
#if defined(FC_BOARD_xiao_rp2040)
#include "board_xiao_rp2040.h"
#else
#include "board_pico.h"      /* pico and pico2 share the wiring */
#endif
