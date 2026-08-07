#include <inttypes.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

uint64_t omega_dot_u64_indexed(const uint64_t *a, const uint64_t *b, size_t n);
uint64_t omega_dot_u64_ptr(const uint64_t *a, const uint64_t *b, size_t n);

static uint64_t reference_dot(const uint64_t *a, const uint64_t *b, size_t n) {
    uint64_t acc = 0;
    for (size_t i = 0; i < n; ++i) {
        acc += a[i] * b[i];
    }
    return acc;
}

static uint64_t xorshift64(uint64_t *state) {
    uint64_t x = *state;
    x ^= x << 13;
    x ^= x >> 7;
    x ^= x << 17;
    *state = x;
    return x;
}

static int check_case(const uint64_t *a, const uint64_t *b, size_t n) {
    const uint64_t expected = reference_dot(a, b, n);
    const uint64_t indexed = omega_dot_u64_indexed(a, b, n);
    const uint64_t ptr = omega_dot_u64_ptr(a, b, n);
    if (expected != indexed || expected != ptr) {
        fprintf(
            stderr,
            "mismatch n=%zu expected=%" PRIu64 " indexed=%" PRIu64 " ptr=%" PRIu64 "\n",
            n,
            expected,
            indexed,
            ptr
        );
        return 1;
    }
    return 0;
}

int main(void) {
    uint64_t a[64] = {0};
    uint64_t b[64] = {0};

    if (check_case(a, b, 0)) return 1;
    a[0] = 3; b[0] = 7;
    if (check_case(a, b, 1)) return 1;

    uint64_t state = UINT64_C(0x9e3779b97f4a7c15);
    for (size_t round = 0; round < 257; ++round) {
        for (size_t i = 0; i < 64; ++i) {
            a[i] = xorshift64(&state);
            b[i] = xorshift64(&state);
        }
        const size_t n = round % 65;
        if (check_case(a, b, n)) return 1;
    }

    puts("omega-asm native differential verification: ok");
    return 0;
}
