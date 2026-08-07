# Ω-ASM-T∞ R2 — P5 Hardware-Counter Foundation

**Status:** stacked research branch on top of PR #352.  
**Authority:** `review_only`.  
**Dependency:** R1 must become green/review-complete before R2 is eligible for merge.

## Mission

R2 begins the transition from observational timing (P4) to target-machine characterization (P5) without collapsing heuristics, measurements and proofs into one score.

```text
P0 specification
-> P1 static structure
-> P2 versioned uncalibrated heuristic
-> P3 native differential correctness
-> P4 observational timing
-> P5 hardware-counter characterization
-> P6 replicated identified-target benchmark
-> P7 formal/SMT certificate
```

The P5 layer answers questions such as:

- how many retired instructions were observed?;
- how many cycles were counted?;
- what IPC follows from those two observations?;
- how many branches/misses and cache references/misses were observed?;
- which CPU/cache/ISA context produced those observations?;
- which exact measured binary produced the evidence?;
- was counter collection unavailable because of runner/kernel permissions?

It does **not** answer “which implementation is universally faster?”.

## Trust boundary

The package deliberately does not expose an API that executes arbitrary commands through `perf`.

```text
repository-controlled native fixture
-> controlled CI shell step
-> perf stat (optional, read-only observation)
-> captured stderr/CSV
-> omega_asm_t.counters parser
-> P5 report
```

Therefore:

- `omega_asm_t.counters` parses evidence but never spawns `perf`;
- arbitrary user-supplied assembly remains non-executable by the trusted default path;
- arbitrary user-supplied shell commands remain non-executable by the package;
- unsupported/not-counted counters become `skipped_events`, never zero;
- permission failure becomes `availability = unavailable`;
- the P5 job has no performance threshold requiring ASM to beat C.

## Microarchitecture manifest

`omega_asm_t.microarch.microarchitecture_manifest()` gathers best-effort observational provenance from standard OS surfaces.

Typical fields:

```text
architecture
vendor / family / model / stepping / model_name
logical CPU count
observed physical core/socket count
ISA feature set
hypervisor flag
cache descriptors from sysfs
frequency/governor context when exposed
OS/kernel/platform
GitHub Actions runner context
optional toolchain versions
```

Missing information remains `null` or empty. It is never guessed.

### Cache descriptors

Each cache entry may carry:

```text
level
type
size_bytes
line_size_bytes
ways_of_associativity
number_of_sets
shared_cpu_list
```

This creates a machine-readable base for later cache-aware scheduling, blocking and vectorization research.

## Toolchain provenance

Optional toolchain capture records availability, resolved path and first `--version` line for:

```text
cc
gcc
clang
as
ld
rustc
```

R2 does not infer semantic equivalence from toolchain identity. Versions are provenance only.

## P5 parser

The canonical collection format is intended to be:

```bash
LC_ALL=C perf stat --no-big-num -x ';' \
  -e cycles,instructions,branches,branch-misses,cache-references,cache-misses,task-clock,context-switches,page-faults \
  <repository-controlled-binary>
```

The parser accepts the captured text and records:

- successful counters;
- unsupported/not-counted events;
- diagnostics;
- event running percentage where reported.

It rejects negative/non-finite values and does not double-count duplicate event rows.

## Derived metrics

For available denominators, P5 derives:

```text
IPC = instructions / cycles
CPI = cycles / instructions
branch_miss_rate = branch_misses / branches
cache_miss_rate = cache_misses / cache_references
```

Undefined ratios remain `null`.

No derived metric changes the OAK authority level.

## Binary provenance

When a measured binary path is supplied, the report records:

```text
path
exists
size_bytes
sha256
```

The SHA-256 is required for future P6 replication: two benchmark records that do not identify the measured artifact should not be treated as measurements of the same binary.

## Availability semantics

P5 distinguishes:

### `available`
At least one hardware counter from the canonical hardware set was parsed.

### `partial`
Counters were parsed, but no canonical hardware event was available (for example only `task-clock`).

### `unavailable`
No usable counter was obtained. Reasons can include:

- `perf` absent;
- kernel policy;
- container/VM restrictions;
- event unsupported;
- permission denied.

Unavailable evidence is a valid report state, not a test failure by itself.

## CLI

```bash
omega-asm microarch
omega-asm microarch --toolchains
omega-asm p5-events
omega-asm p5-report /tmp/perf-stat.csv --exit-code 0
omega-asm p5-report /tmp/perf-stat.csv --binary /tmp/omega-asm-benchmark --exit-code 0
```

The pre-existing R1 surface remains intact.

## Schemas

R2 adds:

```text
schemas/omega_asm_microarch.schema.json
schemas/omega_asm_p5_report.schema.json
policies/omega_asm_t_r2_policy.json
```

The P5 schema fixes the semantics of:

- evidence level;
- availability;
- authority;
- binary provenance;
- counter values;
- skipped events;
- diagnostics;
- derived metrics;
- collection contract.

## CI contract

The R2 court should:

1. run all R1 courts plus the R2 P5 tests;
2. validate both new schemas;
3. compile the trusted native benchmark;
4. attempt `perf stat` only if `perf` exists;
5. always create a P5 report, even when collection is unavailable;
6. validate report structure;
7. require finite non-negative counter values when counters exist;
8. require binary SHA-256 provenance when the binary exists;
9. never require an ASM speed win;
10. keep GitHub token permissions read-only.

## OAK anti-claims / M−

- IPC is not “processor efficiency” in a universal sense.
- Fewer cycles on one hosted runner are not a law about an ISA.
- Cache miss rate without workload/size/layout context is incomplete evidence.
- `perf` denial is not evidence of zero misses or zero cycles.
- Toolchain identity is not correctness proof.
- Hypervisor presence can materially affect timing/counter interpretation.
- Counter multiplexing/running percentage must remain visible.
- A P5 report is not P6 replication.
- A P6 benchmark is not P7 formal equivalence.

## Next R2 increments

After this foundation is green:

1. repeated P5 collection across identified target machines;
2. frequency/turbo/governor controls where accessible;
3. binary/disassembly hashing and compiler-flag ledger;
4. scalar unroll/scheduling families;
5. AVX2/AVX-512 feature-gated variants;
6. native AArch64/NEON validation;
7. C/C++/Rust/ASM compiler parallax;
8. calibrated target-specific cost profiles with uncertainty;
9. bounded bit-vector superoptimization;
10. replayable SMT equivalence evidence.
