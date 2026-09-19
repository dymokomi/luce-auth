/* Test oracle only: distinguish host leaks failures from native codegen/runtime. */
#include <stdio.h>
int main(void) { puts("PASS C heap instrumentation canary"); return 0; }
