/* Runner for the per-group mapper tests (test/tm_*.c). */
#include <stdio.h>
#define GROUPS X(unl)
#define X(g) void tm_##g(int *, int *);
GROUPS
#undef X
int main(void) {
    int checks = 0, fails = 0;
#define X(g) tm_##g(&checks, &fails);
    GROUPS
#undef X
    printf("%d checks, %d failures\n", checks, fails);
    return fails ? 1 : 0;
}
