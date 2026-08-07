# Ω-ASM-T∞ — P4 Observational Benchmark Protocol

## Purpose

P4 answers a narrow question:

> On this recorded execution context, how did the trusted built-in kernels behave under this exact timing protocol?

It does **not** establish universal speedup, energy efficiency, superiority across CPUs, or microarchitectural optimality.

## Evidence ladder

```text
P0 specification
P1 static structure and metrics
P2 heuristic ranking
P3 native differential correctness
P4 observational timing on one execution context
P5 hardware-counter characterization
P6 replicated target-machine benchmark
P7 formal certificate / proof-carrying optimization
```

No score automatically promotes evidence between levels.

## Protocol versions and M− invalidation ledger

### P4 protocol v1 — invalidated for performance comparison

The first successful native P4 execution on 2026-08-07 exposed a benchmark-design defect rather than a credible 193–237x C speed advantage.

Observed medians on that hosted runner were approximately:

```text
reference_c       12.15 ns / 4096-element call
x86_64_indexed  2348.354 ns / call
x86_64_ptr      2883.961 ns / call
```

The C value is incompatible with the intended workload: the optimizer could identify `reference_dot` as side-effect-free with invariant `a`, `b` and `n`, then hoist/reuse the result across the 127 inner repetitions. The external assembly functions did not receive the same optimization because the compiler must conservatively treat them as opaque calls.

Therefore:

```text
P4-v1 timing ratios = INVALIDATED
P3 native correctness = UNAFFECTED
```

Those v1 timings must not be used to calibrate P2, promote P5/P6 evidence, or claim C/ASM performance.

This incident is retained as M− because it demonstrates a general benchmark hazard: **semantic equality of workloads is insufficient when the compiler can optimize the measurement harness asymmetrically**.

### P4 protocol v2 — anti-hoist contract

The native raw report now records:

```text
benchmark_protocol_version = 2
anti_hoist_memory_barrier = true
checksum_scheme = rotate-xor-index-v2
```

Protocol v2 inserts an opaque compiler memory barrier immediately before and after every timed function call. For GCC/Clang this is an empty volatile inline-assembly statement with a `memory` clobber. The portable fallback uses a C11 signal fence.

The barrier is part of the benchmark semantics: it prevents the optimizer from assuming that memory read by a pure C reference remains unchanged across repeated iterations, so the C call cannot legitimately be hoisted out of the INNER loop while external ASM remains repeated.

The checksum also uses an iteration-dependent rotate/mix recurrence instead of pairwise XOR so repeated equal function results cannot collapse into a trivially cancelling checksum pattern.

## Native fixture

`examples/native/omega_dot_u64_benchmark.c` benchmarks three implementations of the same `uint64_t` dot product:

- optimized C reference;
- x86-64 indexed assembly;
- x86-64 pointer assembly.

Before timing, both assembly kernels must equal the C reference on the benchmark data.

## Anti-illusion controls — protocol v2

1. deterministic SplitMix64 input generation;
2. correctness gate before timing;
3. warmup before measurement;
4. `CLOCK_MONOTONIC_RAW` timing;
5. 31 rounds;
6. 127 inner calls per sample;
7. no-inline boundaries around the C reference and timing wrapper on GCC/Clang;
8. **opaque memory barrier around every timed call**;
9. rotating implementation order across rounds;
10. iteration-dependent rotate/xor checksum sink;
11. explicit protocol/version metadata in the raw evidence;
12. no CI threshold asserting that one implementation must be faster.

## Robust statistics

`omega_asm_t.benchmark.summarize_samples` records:

```text
count
minimum
median
mean
maximum
standard deviation
MAD = median absolute deviation
p05
p95
```

Median and MAD are first-class because shared CI runners can contain scheduler, frequency, virtualization and co-tenancy noise.

## Machine provenance

`omega-asm machine` records a dependency-free manifest containing at least:

- architecture;
- CPU model when exposed by the operating system;
- logical CPU count;
- operating system and release;
- platform string;
- Python version and implementation;
- byte order;
- explicit timing claim scope.

The R2 `microarch` surface adds stronger hardware provenance, but neither manifest makes one hosted-run timing universal.

## Report compilation

The native harness emits raw timing samples. They are transformed with:

```bash
omega-asm benchmark-report raw-native.json --output p4-report.json
```

The derived report contains:

- execution-context manifest;
- native metadata, including protocol-v2 anti-hoist markers;
- robust statistics for each implementation;
- median timing ratios relative to the C reference;
- an explicit warning limiting interpretation to the observed context.

Its contract is described by `schemas/omega_asm_benchmark_report.schema.json`.

## Interpretation rule

For an implementation `i`, the displayed ratio is

```text
rho_i = median(T_i) / median(T_reference_c)
```

`rho_i < 1` means it was faster in the observed **valid protocol** sample distribution; `rho_i > 1` means slower. Neither case is generalized outside the recorded context without P6 replication.

A ratio from an invalidated protocol version has no ranking authority regardless of its magnitude.

## What CI may fail on

CI may fail if:

- native correctness fails;
- the benchmark cannot execute;
- protocol-v2 anti-hoist metadata is absent;
- timing samples are missing, negative or non-finite;
- report structure is invalid;
- evidence scope or authority metadata is weakened.

CI must **not** fail because a particular assembly variant is slower than another on a hosted runner.

## Next evidence upgrades

P5 adds controlled hardware-counter collection where permitted. P6 groups replicated evidence only when machine identity and exact binary SHA-256 match. P7 remains a separate formal-equivalence axis.

Performance-model calibration must consume only evidence whose benchmark protocol is not invalidated.
