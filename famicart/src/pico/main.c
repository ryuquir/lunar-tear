/* famicart firmware entry point. */
#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "hardware/clocks.h"
#include "hardware/vreg.h"
#include "board.h"
#include "bus.h"
#include "romslot.h"
#include "../core/cartload.h"
#include "../core/mapper.h"
#include "usb_cmd.h"
#include <stdio.h>

void audio_out_init(void); void audio_out_pump(void); uint32_t audio_sample_rate(void);

static cart_t cart;
static rom_info_t info;
static uint32_t g_len; static const cart_profile_t *g_prof; static load_result_t g_r; static bool g_running;
static const char *src_name(rom_source_t s) {
    switch (s) { case ROM_SRC_DB: return "database(CRC32)"; case ROM_SRC_NES20: return "NES 2.0 header"; case ROM_SRC_INES: return "iNES header"; case ROM_SRC_HEURISTIC: return "heuristic"; default: return "none"; }
}

int main(void) {
    vreg_set_voltage(VREG_VOLTAGE_1_15);
    sleep_ms(2);
    set_sys_clock_khz(FC_SYS_CLOCK_KHZ, true);
    stdio_init_all();

    const uint8_t *img = romslot_image(&g_len, &g_prof);
    g_r = cart_load(&cart, img, g_len, g_prof, &info);

    if (g_r == LOAD_OK) {
        audio_out_init();
#if FC_BUS_CAPABLE
        bus_init(&cart);
        g_running = true;
#endif
    }
    usb_cmd_init();

    absolute_time_t next_report = make_timeout_time_ms(1000);
    for (;;) {
        if (g_r == LOAD_OK) audio_out_pump();
        usb_cmd_poll();
        if (time_reached(next_report)) { next_report = make_timeout_time_ms(10000); usb_cmd_print_info(); }
    }
}

void usb_cmd_print_info(void) {
    printf("\n[famicart] board=%s sysclk=%lu kHz\n", FC_BUS_CAPABLE ? "bus-capable" : "no-bus (XIAO)", clock_get_hz(clk_sys) / 1000);
    printf("  image: %lu bytes @slot, profile=%s\n", (unsigned long)g_len, g_prof ? "yes" : "none");
    printf("  load : %s\n", cart_load_strerror(g_r));
    printf("  rom  : src=%s mapper=%u sub=%u prg=%luK chr=%luK chrram=%luK wram=%luK sram=%luK mirror=%u batt=%d crc=%08lX %s\n",
           src_name(info.source), info.mapper, info.submapper, (unsigned long)info.prg_size / 1024, (unsigned long)info.chr_size / 1024,
           (unsigned long)info.chr_ram_size / 1024, (unsigned long)info.wram_size / 1024, (unsigned long)info.sram_size / 1024,
           info.mirroring, info.battery, (unsigned long)info.crc32, info.note);
    if (g_r == LOAD_OK) printf("  cart : %s (id %u) audio_mask=%02X irq=%u\n", cart.mapper->name, cart.mapper_id, cart.audio_mask, cart.irq_line);
    if (g_running) printf("  bus  : m2=%lu rd=%lu wr=%lu ppu_rd=%lu ppu_wr=%lu\n", (unsigned long)bus_stat_cpu_cycles, (unsigned long)bus_stat_cpu_reads,
                          (unsigned long)bus_stat_cpu_writes, (unsigned long)bus_stat_ppu_reads, (unsigned long)bus_stat_ppu_writes);
    printf("  cmds : INFO | RESET | BOOTSEL | LOAD <bytes> [crc32] | PROFILE <hex>\n");
}
