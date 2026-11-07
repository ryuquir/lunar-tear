CC ?= gcc
CFLAGS ?= -std=c11 -O1 -g -Wall -Wextra -Wno-unused-parameter -fsanitize=address,undefined -I../src/core -DFC_ROM_POOL_SIZE=2097152 -DFC_RAM_POOL_SIZE=131072
LDLIBS = -lm
CORE := $(wildcard ../src/core/*.c) $(wildcard ../src/core/mappers/*.c) $(wildcard ../src/core/audio/*.c)
REVE := $(wildcard ../src/core/reve/*.c)
all: test_core test_virtual test_reve
	./test_core
	./test_virtual
	./test_reve
test_core: test_core.c $(CORE)
	$(CC) $(CFLAGS) -o $@ $^ $(LDLIBS)
test_virtual: test_virtual.c $(CORE)
	$(CC) $(CFLAGS) -DFC_VIRTUAL_ROM=1 -o $@ $^ $(LDLIBS)
test_reve: test_reve.c $(CORE) $(REVE)
	$(CC) $(CFLAGS) -o $@ $^ $(LDLIBS)
clean:
	rm -f test_core test_virtual test_reve
.PHONY: all clean
