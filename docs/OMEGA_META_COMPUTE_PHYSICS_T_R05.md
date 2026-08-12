# Ω-META-COMPUTE-PHYSICS-T∞ — R0.5 Fleet Execution

## Status

**D-MVP candidate.** R0.5 extends the green R0.4 meta-discovery stack with a
static-first cross-repository execution protocol. Dynamic benchmarking remains
contract-gated and is never treated as sandboxed merely because a timeout or
subprocess boundary exists.

## Mother loop

```text
GitHub fleet
-> pinned local checkouts
-> Stage A static RepositoryGenome
-> Complexity-IR
-> workload families
-> global benchmark priority
-> typed BenchmarkContract
-> OAK gate
-> controlled measurement environment
-> ResourceSamples
-> validated empirical laws + uncertainty
-> Representation Generator / Theory Ecology / Residual Intelligence
-> tropical multivariate dominance map
-> DAG resource composition
-> cross-commit / cross-repo evidence
-> repeat
```

## 1. BenchmarkContract-T

`omega_compute_physics_t/benchmark_contract.py`

A dynamic measurement request is represented explicitly by:

```text
(repository, commit_sha, module, callable, axes, fixture,
 repeats, warmups, timeout, max_cases, trust flag, risk vector)
```

The gate rejects by default:

- unpinned repository/commit identity;
- untrusted checkout;
- unbounded design sizes;
- network use;
- credentials;
- destructive I/O;
- external side effects;
- privileged operations.

An `allow` result means **policy-compatible candidate**, not secure sandbox.
External containment remains a separate infrastructure concern.

## 2. Complexity-IR-T

`omega_compute_physics_t/complexity_ir.py`

The first IR vocabulary includes:

```text
LOAD STORE ARITH COMPARE INDEX CALL LOOP BRANCH
ALLOC COMPREHENSION AWAIT YIELD
```

Each function receives syntax-level counts, maximum loop depth and call targets.
These counts are useful for workload similarity and measurement design but are
not direct FLOP, byte, cycle or asymptotic-complexity counts.

Future R0.6 evolution can add calibrated motifs such as MATMUL, REDUCE,
IRREGULAR_GATHER, TRANSFER and SYNC only when a reliable recognizer exists.

## 3. MachineGenome-T

`omega_compute_physics_t/machine_genome.py`

Portable fingerprint fields include system, kernel/release, machine,
processor string, Python version, logical CPUs, page size, physical-memory
estimate and load average where available.

Optional bounded calibration measures two local empirical fingerprints:

- scalar Python-loop throughput;
- bytearray copy throughput.

These values are not hardware peak specifications. They characterize the
current host/process/software state and must be versioned with evidence.

## 4. DAG Resource Physics

`omega_compute_physics_t/dag_resources.py`

Pipelines are represented as DAG nodes plus transfer edges.

For supplied duration estimates the scheduler-independent lower planning model
computes a longest weighted dependency path:

```text
T_critical = max dependency-path cost
```

It also reports serial-sum cost and a deliberately conservative memory-liveness
proxy from outputs, edge buffers and largest node peak.

The module rejects cycles rather than silently applying DAG mathematics to a
cyclic workflow.

Contention, allocator reuse, overlap and machine scheduling remain empirical
quantities.

## 5. Tropical Complexity Geometry

`omega_compute_physics_t/tropical.py`

For an active monomial term

```text
c_alpha x^alpha
```

and anisotropic path

```text
x_i = lambda ** v_i,
```

its directional exponent is

```text
p_alpha(v) = alpha dot v.
```

Inside the supplied symbolic model the dominant candidate degree is

```text
p(v) = max_alpha alpha dot v.
```

This gives a geometric answer to multivariate scaling: different asymptotic
directions can expose different dominant monomials. The exponent vectors form
the model's Newton support; dominance changes define polyhedral/tropical
boundaries in log-size space.

OAK boundary: this is exact mathematics **for the supplied fitted symbolic
model**. It is not automatically a theorem about the implementation.

## 6. Fleet Stage A

`omega_compute_physics_t/fleet_stage_a.py`

Stage A consumes a mapping of repository names to pinned local checkout paths.
It performs no imports and executes no repository functions.

Output:

- per-repository Python file/function/LOC inventory;
- max loop depth, recursion and async summaries;
- cross-repository workload families;
- globally ranked benchmark seeds.

Example:

```bash
python -m omega_compute_physics_t.fleet_cli stage-a \
  --repo TFUGA=/checkouts/TFUGA-AI7-TRISTAN2 \
  --repo TFACC=/checkouts/TFACC \
  --output fleet_stage_a.json
```

Machine fingerprint:

```bash
python -m omega_compute_physics_t.fleet_cli machine --calibrate
```

Benchmark policy gate:

```bash
python -m omega_compute_physics_t.fleet_cli gate-contract contract.json
```

## 7. Six-repository Tristan rollout

The connected GitHub fleet currently exposes these rollout targets:

```text
Tristan-TM-Poly/PEFA-FractalEnergySystem
Tristan-TM-Poly/Tristan_Tardif-Morency_TFUG
Tristan-TM-Poly/Tristan_Tardif-Morency_TFUGAG
Tristan-TM-Poly/TFACC
Tristan-TM-Poly/TFUGA-AI7-TRISTAN2
Tristan-TM-Poly/TTM-TFUGA-AI7-TRISTAN2
```

The repository already contains
`complexity_atlas/fleet_rollout_manifest_v0_1.json` as the Stage A seed.

Remote code search already shows Python surfaces in multiple repositories;
Stage A is designed to replace ad-hoc search with complete local pinned-checkout
analysis.

## 8. Cross-repository transfer rule

A workload family in repository A may provide a **prior** for repository B.
It may not automatically provide a validated law for B.

Required promotion sequence:

```text
static similarity
-> prior candidate
-> destination measurements
-> held-out validation
-> uncertainty calibration
-> optional transfer promotion
```

This prevents similarity from becoming false universality.

## 9. Evidence ladder

```text
L0 static structural hint
L1 bounded measurement
L2 held-out empirical validation
L3 repeated/multi-environment validation
L4 mechanism-backed performance explanation
L5 mathematical bound
L6 formal proof
```

R0.5 primarily strengthens L0-L3 infrastructure.

## 10. R0.6 frontier

The next high-value tranche should be kept narrow:

1. repository adapters that materialize pinned read-only checkouts;
2. benchmark fixture registry and typed argument generators;
3. isolated-runner adapter with externally provided sandbox/container support;
4. Complexity-IR call/dependency graph linking;
5. measured DAG node/edge calibration;
6. per-repository Stage A reports for all six repos;
7. first bounded Stage B campaign on a small set of deterministic pure functions;
8. fleet-wide Complexity Diff and confidence-aware regression ledger.

Do not expand dynamic execution faster than the evidence and containment model.
