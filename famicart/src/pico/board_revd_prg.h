/* famicart rev D, U1 "PRG mapper / expansion chip" (RP2350B). Sits on the 3.3 V local bus; the PRG flash and the
 * F-RAM answer the console directly, this MCU only drives their bank/select lines, serves $4020-$5FFF itself
 * and runs the expansion-audio synth. */
#pragma once
#define FC_BUS_CAPABLE        0      /* bus.c (rev A-C data-serving front-ends) compiled out; bus_revd.c instead */
#define FC_BUS_REVD           1
#define FC_VIRTUAL_ROM        1
#define FC_ROLE_PRG           1

#define PIN_CPU_BASE          0      /* GPIO0-25: CA0-14, CD0-7, CRW, CM2, CnROMSEL (same order as rev C) */
#define PIN_CPU_DATA_BASE     15
#define PIN_CPU_RW            23
#define PIN_CPU_M2            24
#define PIN_CPU_ROMSEL        25
#define PIN_NDRIVE            26     /* low: our data reaches the console (74LVC245 enable) */
#define PIN_PRG_BANK_BASE     27     /* GPIO27-39 = PRG flash / F-RAM A13-A25 */
#define PIN_PRG_BANK_BITS     13
#define PIN_WRAM_NCE          40
#define PIN_IRQ               41     /* through a 74LVC1G07 open-drain buffer */
#define PIN_AUDIO_PWM         42
#define PIN_LINK_CLK          43     /* -> U2 */
#define PIN_LINK_DATA         44     /* -> U2 */
#define PIN_LINK_RX           45     /* <- U2 (PIO UART, 2 Mbaud) */
#define PIN_PRG_NWE           46
#define PIN_ISOLATE           47     /* high: all 74LVC541/245 towards the console disabled */
#define PIN_CIRAM_A10         (-1)
#define PIN_CIRAM_CE          (-1)
#define PIN_UART_TX           (-1)

#define FC_SYS_CLOCK_KHZ      150000
#define FC_FLASH_ROM_SLOT     0x00100000u   /* U1 QSPI: ROM library index (not the ROM itself) */
#define FC_FLASH_ROM_SLOT_MAX 0x00100000u
#define FC_BOOT_BANK          0x1FFFu       /* top 8 KB bank of the 64 MB PRG flash = boot stub */
