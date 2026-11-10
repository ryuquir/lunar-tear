CC ?= gcc
CFLAGS ?= -std=c11 -O1 -g -Wall -Wextra -Wno-unused-parameter -fsanitize=address,undefined -I../src/core -DFC_ROM_POOL_SIZE=2097152 -DFC_RAM_POOL_SIZE=131072
LDLIBS = -lm
CORE := $(wildcard ../src/core/*.c) $(wildcard ../src/core/mappers/*.c) $(wildcard ../src/core/audio/*.c)
REVE := $(wildcard ../src/core/reve/*.c) $(wildcard ../src/core/coproc/*.c)
HDR := $(wildcard ../src/core/*.h ../src/core/*/*.h) tm_util.h
all: test_core test_virtual test_reve test_mappers
	./test_core
	./test_virtual
	./test_reve
	./test_mappers
test_core: test_core.c $(CORE) $(HDR)
	$(CC) $(CFLAGS) -o $@ $(filter %.c,$^) $(LDLIBS)
test_virtual: test_virtual.c $(CORE) $(HDR)
	$(CC) $(CFLAGS) -DFC_VIRTUAL_ROM=1 -o $@ $(filter %.c,$^) $(LDLIBS)
test_reve: test_reve.c $(CORE) $(REVE) $(HDR)
	$(CC) $(CFLAGS) -o $@ $(filter %.c,$^) $(LDLIBS)
TM := tm_unl.c tm_multi.c tm_mmc3x.c tm_lic.c tm_bandai_ee.c tm_coproc.c tm_m030.c tm_ram.c
test_mappers: test_mappers.c $(TM) $(CORE) $(REVE) $(HDR)
	$(CC) $(CFLAGS) -o $@ $(filter %.c,$^) $(LDLIBS)
clean:
	rm -f test_core test_virtual test_reve test_mappers
.PHONY: all clean
