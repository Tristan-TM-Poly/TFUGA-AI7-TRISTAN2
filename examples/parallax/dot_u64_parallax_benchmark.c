#define _POSIX_C_SOURCE 200809L
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

uint64_t omega_dot_u64_c(const uint64_t *, const uint64_t *, uint64_t);
uint64_t omega_dot_u64_cpp(const uint64_t *, const uint64_t *, uint64_t);
uint64_t omega_dot_u64_rust(const uint64_t *, const uint64_t *, uint64_t);
uint64_t omega_dot_u64_indexed(const uint64_t *, const uint64_t *, uint64_t);
uint64_t omega_dot_u64_ptr(const uint64_t *, const uint64_t *, uint64_t);

typedef uint64_t (*kernel_fn)(const uint64_t *, const uint64_t *, uint64_t);

#if defined(__GNUC__) || defined(__clang__)
#define OMEGA_NOINLINE __attribute__((noinline))
#define OMEGA_MEMORY_BARRIER() __asm__ __volatile__("" ::: "memory")
#else
#define OMEGA_NOINLINE
#define OMEGA_MEMORY_BARRIER() ((void)0)
#endif

static uint64_t splitmix64(uint64_t *state) {
    uint64_t z = (*state += UINT64_C(0x9e3779b97f4a7c15));
    z = (z ^ (z >> 30)) * UINT64_C(0xbf58476d1ce4e5b9);
    z = (z ^ (z >> 27)) * UINT64_C(0x94d049bb133111eb);
    return z ^ (z >> 31);
}

static uint64_t nanoseconds(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC_RAW, &ts) != 0) exit(3);
    return (uint64_t)ts.tv_sec * UINT64_C(1000000000) + (uint64_t)ts.tv_nsec;
}

static uint64_t mix(uint64_t state, uint64_t result, unsigned i) {
    state = (state << 9) | (state >> 55);
    return state ^ result ^ (UINT64_C(0x517cc1b727220a95) + i);
}

static OMEGA_NOINLINE double measure(kernel_fn fn, const uint64_t *a, const uint64_t *b,
                                     uint64_t n, unsigned inner, volatile uint64_t *sink) {
    uint64_t local = UINT64_C(0x3243f6a8885a308d);
    uint64_t start = nanoseconds();
    for (unsigned i = 0; i < inner; ++i) {
        OMEGA_MEMORY_BARRIER();
        uint64_t result = fn(a, b, n);
        OMEGA_MEMORY_BARRIER();
        local = mix(local, result, i);
    }
    uint64_t stop = nanoseconds();
    *sink ^= local;
    return (double)(stop - start) / (double)inner;
}

static void print_samples(const char *name, const double *samples, unsigned count) {
    printf("\"%s\":[", name);
    for (unsigned i = 0; i < count; ++i) {
        if (i) putchar(',');
        printf("%.3f", samples[i]);
    }
    putchar(']');
}

int main(void) {
    enum { N = 4096, ROUNDS = 31, INNER = 127, VARIANTS = 5 };
    uint64_t *a = malloc((size_t)N * sizeof(*a));
    uint64_t *b = malloc((size_t)N * sizeof(*b));
    if (!a || !b) return 2;
    uint64_t seed = UINT64_C(0x706172616c6c6178);
    for (unsigned i = 0; i < N; ++i) {
        a[i] = splitmix64(&seed);
        b[i] = splitmix64(&seed);
    }

    struct variant {
        const char *name;
        kernel_fn fn;
        double samples[ROUNDS];
    } variants[VARIANTS] = {
        {"reference_c", omega_dot_u64_c, {0}},
        {"cpp", omega_dot_u64_cpp, {0}},
        {"rust", omega_dot_u64_rust, {0}},
        {"asm_indexed", omega_dot_u64_indexed, {0}},
        {"asm_ptr", omega_dot_u64_ptr, {0}},
    };

    uint64_t expected = omega_dot_u64_c(a, b, N);
    for (unsigned v = 1; v < VARIANTS; ++v) {
        if (variants[v].fn(a, b, N) != expected) {
            fprintf(stderr, "correctness gate failed for %s\n", variants[v].name);
            return 4;
        }
    }

    volatile uint64_t sink = expected ^ UINT64_C(0xbb67ae8584caa73b);
    for (unsigned round = 0; round < ROUNDS; ++round) {
        unsigned start = round % VARIANTS;
        for (unsigned offset = 0; offset < VARIANTS; ++offset) {
            unsigned v = (start + offset) % VARIANTS;
            variants[v].samples[round] = measure(variants[v].fn, a, b, N, INNER, &sink);
        }
    }

    printf("{\"schema_version\":1,\"benchmark_protocol_version\":2,"
           "\"evidence_level\":\"P4-observational\","
           "\"claim_scope\":\"single_execution_context_only\","
           "\"parallax\":true,\"separate_translation_units\":true,"
           "\"anti_hoist_memory_barrier\":true,"
           "\"elements\":%u,\"rounds\":%u,\"inner_iterations\":%u,"
           "\"checksum\":\"%016" PRIx64 "\",\"samples_ns_per_call\":{",
           (unsigned)N, (unsigned)ROUNDS, (unsigned)INNER, (uint64_t)sink);
    for (unsigned v = 0; v < VARIANTS; ++v) {
        if (v) putchar(',');
        print_samples(variants[v].name, variants[v].samples, ROUNDS);
    }
    puts("}}");
    free(a);
    free(b);
    return 0;
}
