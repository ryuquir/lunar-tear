cmake_minimum_required(VERSION 3.13)
# Target board: pico (RP2040, 27-pin buffered scheme) | pico2 (RP2350A, same wiring, 520K SRAM) | xiao_rp2040 (no bus: loader/audio role only)
set(FC_BOARD "pico" CACHE STRING "famicart board profile")
if(FC_BOARD STREQUAL "pico2")
  set(PICO_BOARD pico2 CACHE STRING "" FORCE)
  set(PICO_PLATFORM rp2350-arm-s CACHE STRING "" FORCE)
elseif(FC_BOARD STREQUAL "xiao_rp2040")
  set(PICO_BOARD seeed_xiao_rp2040 CACHE STRING "" FORCE)
else()
  set(PICO_BOARD pico CACHE STRING "" FORCE)
endif()
include(pico_sdk_import.cmake)
project(famicart C CXX ASM)
set(CMAKE_C_STANDARD 11)
pico_sdk_init()

file(GLOB CORE_SRC src/core/*.c src/core/mappers/*.c src/core/audio/*.c)
add_executable(famicart
  ${CORE_SRC}
  src/pico/main.c
  src/pico/bus.c
  src/pico/audio_out.c
  src/pico/romslot.c
)
pico_generate_pio_header(famicart ${CMAKE_CURRENT_LIST_DIR}/src/pico/fc_bus.pio)
target_include_directories(famicart PRIVATE src src/core src/pico)
target_compile_definitions(famicart PRIVATE PICO_BUILD=1 FC_BOARD_${FC_BOARD}=1)
if(FC_BOARD STREQUAL "pico2")
  target_compile_definitions(famicart PRIVATE FC_ROM_POOL_SIZE=450560 FC_RAM_POOL_SIZE=49152)   # 440K + 48K of 520K
else()
  target_compile_definitions(famicart PRIVATE FC_ROM_POOL_SIZE=200704 FC_RAM_POOL_SIZE=45056)   # 196K + 44K of 264K
endif()
target_compile_options(famicart PRIVATE -O2 -Wall -Wextra -Wno-unused-parameter)
target_link_libraries(famicart pico_stdlib pico_multicore hardware_pio hardware_dma hardware_pwm hardware_flash hardware_irq hardware_clocks)
pico_enable_stdio_usb(famicart 1)
pico_enable_stdio_uart(famicart 0)
pico_add_extra_outputs(famicart)
