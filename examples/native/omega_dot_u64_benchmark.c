#define _POSIX_C_SOURCE 200809L
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

uint64_t omega_dot_u64_indexed(const uint64_t *a, const uint64_t *b, uint64_t n);
uint64_t omega_dot_u64_ptr(const uint64_t *a, const uint64_t *b, uint64_t n);

typedef uint64_t (*kernel_fn)(const uint64_t *, const uint64_t *, uint64_t);

#if defined(__GNUC__) || defined(__clang__)
#define OMEGA_NOINLINE __attribute__((noinline))
#else
#define OMEGA_NOINLINE
#endif

static OMEGA_NOINLINE uint64_t reference_dot(const uint64_t *a, const uint64_t *b, uint64_t n) {
    uint64_t acc = 0;
    for (uint64_t i = 0; i < n; ++i) {
        acc += a[i] * b[i];
    }
    return acc;
}

static uint64_t splitmix64(uint64_t *state) {
    uint64_t z = (*state += UINT64_C(0x9e3779b97f4a7c15));
    z = (z ^ (z >> 30)) * UINT64_C(0xbf58476d1ce4e5b9);
    z = (z ^ (z >> 27)) * UINT64_C(0x94d049bb133111eb);
    return z ^ (z >> 31);
}

static uint64_t nanoseconds(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC_RAW, &ts) != 0) {
        perror("clock_gettime");
        exit(3);
    }
    return (uint64_t)ts.tv_sec * UINT64_C(1000000000) + (uint64_t)ts.tv_nsec;
}

static OMEGA_NOINLINE double measure(kernel_fn fn, const uint64_t *a, const uint64_t *b,
                                     uint64_t n, unsigned inner, volatile uint64_t *sink) {
    uint64_t start = nanoseconds();
    uint64_t local = 0;
    for (unsigned i = 0; i < inner; ++i) {
        local ^= fn(a, b, n);
    }
    uint64_t stop = nanoseconds();
    *sink ^= local;
    return (double)(stop - start) / (double)inner;
}

static void print_samples(const char *name, const double *samples, unsigned count) {
    printf("\"%s\":[", name);
    for (unsigned i = 0; i < count; ++i) {
        if (i) {
            putchar(',');
        }
        printf("%.3f", samples[i]);
    }
    putchar(']');
}

int main(void) {
    enum { N = 4096, ROUNDS = 31, INNER = 127, WARMUP = 64 };
    uint64_t *a = malloc((size_t)N * sizeof(*a));
    uint64_t *b = malloc((size_t)N * sizeof(*b));
    if (!a || !b) {
        fputs("allocation failure\n", stderr);
        free(a);
        free(b);
        return 2;
    }

    uint64_t state = UINT64_C(0x6f6d65676161736d);
    for (unsigned i = 0; i < N; ++i) {
        a[i] = splitmix64(&state);
        b[i] = splitmix64(&state);
    }

    uint64_t expected = reference_dot(a, b, N);
    if (omega_dot_u64_indexed(a, b, N) != expected || omega_dot_u64_ptr(a, b, N) != expected) {
        fputs("correctness gate failed before timing\n", stderr);
        free(a);
        free(b);
        return 4;
    }

    volatile uint64_t sink = expected;
    for (unsigned i = 0; i < WARMUP; ++i) {
        sink ^= reference_dot(a, b, N);
        sink ^= omega_dot_u64_indexed(a, b, N);
        sink ^= omega_dot_u64_ptr(a, b, N);
    }

    double reference_samples[ROUNDS];
    double indexed_samples[ROUNDS];
    double ptr_samples[ROUNDS];
    for (unsigned round = 0; round < ROUNDS; ++round) {
        /* Rotate order to reduce systematic first/last bias. */
        switch (round % 3U) {
            case 0:
                reference_samples[round] = measure(reference_dot, a, b, N, INNER, &sink);
                indexed_samples[round] = measure(omega_dot_u64_indexed, a, b, N, INNER, &sink);
                ptr_samples[round] = measure(omega_dot_u64_ptr, a, b, N, INNER, &sink);
                break;
            case 1:
                indexed_samples[round] = measure(omega_dot_u64_indexed, a, b, N, INNER, &sink);
                ptr_samples[round] = measure(omega_dot_u64_ptr, a, b, N, INNER, &sink);
                reference_samples[round] = measure(reference_dot, a, b, N, INNER, &sink);
                break;
            default:
                ptr_samples[round] = measure(omega_dot_u64_ptr, a, b, N, INNER, &sink);
                reference_samples[round] = measure(reference_dot, a, b, N, INNER, &sink);
                indexed_samples[round] = measure(omega_dot_u64_indexed, a, b, N, INNER, &sink);
                break;
        }
    }

    printf("{\"schema_version\":1,\"evidence_level\":\"P4-observational\","
           "\"claim_scope\":\"single_execution_context_only\","
           "\"elements\":%u,\"rounds\":%u,\"inner_iterations\":%u,\"checksum\":\"%016" PRIx64 "\",\"samples_ns_per_call\":{",
           (unsigned)N, (unsigned)ROUNDS, (unsigned)INNER, (uint64_t)sink);
    print_samples("reference_c", reference_samples, ROUNDS);
    putchar(',');
    print_samples("x86_64_indexed", indexed_samples, ROUNDS);
    putchar(',');
    print_samples("x86_64_ptr", ptr_samples, ROUNDS);
    puts("}}");

    free(a);
    free(b);
    return 0;
}
