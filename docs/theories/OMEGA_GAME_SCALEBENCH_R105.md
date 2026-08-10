# Ω-GAME R1.0.5 — ScaleBench

**Status:** executable scale/measurement candidate after R1.0.4  
**Authority:** deterministic workload accounting plus local empirical observation only

## Purpose

R1.0.5 measures how Omega GAME behaves as campaign workload grows without mixing deterministic provenance with machine-dependent performance claims.

```text
ScaleScenario
→ deterministic campaign plan
→ complete checkpoint
→ repeated campaign benchmark
→ optional process equivalence
→ deterministic work channel
  + empirical measurement channel
```

## Deterministic workload contract

A `ScaleScenario` specifies:

```text
name
seed
population_size
seed_count
max_steps
shard_count
repetitions
process_workers
```

For the current mirrored no-fixed-layout campaign benchmark:

```text
expected_jobs = C(population_size, 2) × seed_count × 2
```

The scenario is accepted only if:

- manifest job count matches this exact formula;
- campaign completes;
- checkpoint contains every job;
- repeated benchmark job count matches;
- deterministic tick work units repeat;
- deterministic event work units repeat;
- optional multi-process execution yields the same deterministic checkpoint.

## Deterministic receipt

The scenario receipt includes:

```text
scenario configuration
accepted flag
invariant checks
job count
match-tick work units
event work units
checkpoint receipt
campaign benchmark receipt
```

It deliberately excludes machine-dependent observations.

## Empirical channel

R1.0.5 separately reports:

```text
single-run wall-clock seconds
median repeated wall-clock seconds
peak tracemalloc bytes
observed process speedup
```

These values are **not hashed into deterministic provenance**.

`tracemalloc` measures Python-tracked allocations, not complete process RSS or GPU/OS memory.

```text
WALL_CLOCK != DETERMINISTIC_PROVENANCE
TRACEMALLOC_PEAK != TOTAL_MEMORY_USAGE
OBSERVED_SPEEDUP != GUARANTEED_SPEEDUP
```

## Built-in matrix

`default_scale_scenarios()` currently provides bounded tiny/small/medium workloads. The matrix is a practical local benchmark set, not a universal scale law.

```text
TESTED_LARGER_WORKLOAD != UNBOUNDED_SCALABILITY
```

## CLI

Single explicit scenario:

```bash
omega-game scale-bench \
  --seed 1801 \
  --population 6 \
  --seed-count 2 \
  --max-steps 8 \
  --shards 3 \
  --repetitions 2 \
  --workers 2
```

Built-in matrix:

```bash
omega-game scale-bench --matrix
```

The command exits non-zero if any deterministic scale invariant fails.

## OAK boundaries

```text
JOB_COUNT_FORMULA != PERFORMANCE_MODEL
WORK_UNITS != CPU_CYCLES
WALL_CLOCK_SAMPLE != GUARANTEED_RUNTIME
TRACEMALLOC_PEAK != TOTAL_PROCESS_MEMORY
PROCESS_EQUIVALENCE != PROCESS_SPEEDUP
OBSERVED_SPEEDUP != GUARANTEED_SPEEDUP
THREE_SCALE_POINTS != ASYMPTOTIC_PROOF
TESTED_LARGER_WORKLOAD != UNBOUNDED_SCALABILITY
```

## Next

Use ScaleBench to collect reproducible workload identities and local empirical observations across larger bounded matrices. Only after multiple machines/runners and repeated measurements should performance hypotheses be promoted. Remote/distributed scalability remains outside the demonstrated capability set.
