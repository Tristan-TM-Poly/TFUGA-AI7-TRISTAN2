#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

uint64_t omega_dot_u64_c(const uint64_t *, const uint64_t *, uint64_t);
uint64_t omega_dot_u64_cpp(const uint64_t *, const uint64_t *, uint64_t);
uint64_t omega_dot_u64_rust(const uint64_t *, const uint64_t *, uint64_t);
uint64_t omega_dot_u64_indexed(const uint64_t *, const uint64_t *, uint64_t);
uint64_t omega_dot_u64_ptr(const uint64_t *, const uint64_t *, uint64_t);

typedef uint64_t (*kernel_fn)(const uint64_t *, const uint64_t *, uint64_t);

static uint64_t reference_dot(const uint64_t *a, const uint64_t *b, uint64_t n) {
    uint64_t acc = 0;
    for (uint64_t i = 0; i < n; ++i) acc += a[i] * b[i];
    return acc;
}

static uint64_t splitmix64(uint64_t *state) {
    uint64_t z = (*state += UINT64_C(0x9e3779b97f4a7c15));
    z = (z ^ (z >> 30)) * UINT64_C(0xbf58476d1ce4e5b9);
    z = (z ^ (z >> 27)) * UINT64_C(0x94d049bb133111eb);
    return z ^ (z >> 31);
}

int main(void) {
    struct variant { const char *name; kernel_fn fn; } variants[] = {
        {"c", omega_dot_u64_c},
        {"cpp", omega_dot_u64_cpp},
        {"rust", omega_dot_u64_rust},
        {"asm_indexed", omega_dot_u64_indexed},
        {"asm_ptr", omega_dot_u64_ptr},
    };
    enum { MAX_N = 257, CAMPAIGNS = 257 };
    uint64_t a[MAX_N], b[MAX_N];
    uint64_t state = UINT64_C(0x706172616c6c6178);

    for (unsigned campaign = 0; campaign < CAMPAIGNS; ++campaign) {
        uint64_t n = campaign % MAX_N;
        for (uint64_t i = 0; i < n; ++i) {
            a[i] = splitmix64(&state);
            b[i] = splitmix64(&state);
        }
        uint64_t expected = reference_dot(a, b, n);
        for (size_t v = 0; v < sizeof(variants) / sizeof(variants[0]); ++v) {
            uint64_t got = variants[v].fn(a, b, n);
            if (got != expected) {
                fprintf(stderr,
                        "parallax mismatch campaign=%u n=%" PRIu64 " implementation=%s expected=%016" PRIx64 " got=%016" PRIx64 "\n",
                        campaign, n, variants[v].name, expected, got);
                return 2;
            }
        }
    }
    puts("omega-asm compiler parallax differential verification: ok");
    return 0;
}
