/* Common types/macros for the portable cartridge core. */
#pragma once
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#if defined(PICO_BUILD)
#include "pico.h"
/* Time-critical code/data is pinned to SRAM so bus service never waits on XIP flash. */
#define FC_FASTCODE  __not_in_flash_func
#define FC_FASTDATA  __not_in_flash("fcdata")
#else
#define FC_FASTCODE(x) x
#define FC_FASTDATA
#endif

#define FC_INLINE static inline __attribute__((always_inline))
#define FC_ARRAY_LEN(a) (sizeof(a) / sizeof((a)[0]))
