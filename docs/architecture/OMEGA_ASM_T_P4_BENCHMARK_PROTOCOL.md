# Ω-ASM-T∞ — P4 Observational Benchmark Protocol

## Purpose

P4 answers a narrow question:

> On this recorded execution context, how did the trusted built-in kernels behave under this timing protocol?

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

## Native fixture

`examples/native/omega_dot_u64_benchmark.c` benchmarks three implementations of the same `uint64_t` dot product:

- optimized C reference;
- x86-64 indexed assembly;
- x86-64 pointer assembly.

Before timing, both assembly kernels must equal the C reference on the benchmark data.

## Anti-illusion controls

R1.1 applies the following controls:

1. deterministic SplitMix64 input generation;
2. correctness gate before timing;
3. warmup before measurement;
4. `CLOCK_MONOTONIC_RAW` timing;
5. 31 independent rounds;
6. 127 inner calls per sample so the XOR checksum cannot cancel pairwise;
7. no-inline boundaries around the C reference and timing wrapper on GCC/Clang;
8. rotating implementation order across rounds;
9. volatile checksum sink to keep results observable;
10. no CI threshold asserting that one implementation must be faster.

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

The manifest is contextual evidence, not a complete microarchitecture fingerprint.

## Report compilation

The native harness emits raw timing samples. They are transformed with:

```bash
omega-asm benchmark-report raw-native.json --output p4-report.json
```

The derived report contains:

- execution-context manifest;
- native metadata;
- robust statistics for each implementation;
- median timing ratios relative to the C reference;
- an explicit warning limiting interpretation to the observed context.

Its contract is described by `schemas/omega_asm_benchmark_report.schema.json`.

## Interpretation rule

For an implementation `i`, the displayed ratio is

```text
rho_i = median(T_i) / median(T_reference_c)
```

`rho_i < 1` means it was faster in the observed sample distribution; `rho_i > 1` means slower. Neither case is generalized outside the recorded context without P6 replication.

## What CI may fail on

CI may fail if:

- native correctness fails;
- the benchmark cannot execute;
- timing samples are missing, negative or non-finite;
- report structure is invalid;
- evidence scope or authority metadata is weakened.

CI must **not** fail because a particular assembly variant is slower than another on a hosted runner.

## Next evidence upgrades

P5 should add controlled hardware-counter collection where permitted:

```text
cycles
instructions
branches
branch-misses
cache references/misses
context switches
page faults
```

P6 should replicate a pinned benchmark protocol on identified target CPUs, record compiler/assembler versions and frequencies, and compare distributions across repeated runs rather than isolated numbers.
