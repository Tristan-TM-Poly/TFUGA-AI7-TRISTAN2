#include <stdint.h>

uint64_t omega_dot_u64_c(const uint64_t *a, const uint64_t *b, uint64_t n) {
    uint64_t acc = 0;
    for (uint64_t i = 0; i < n; ++i) {
        acc += a[i] * b[i];
    }
    return acc;
}
