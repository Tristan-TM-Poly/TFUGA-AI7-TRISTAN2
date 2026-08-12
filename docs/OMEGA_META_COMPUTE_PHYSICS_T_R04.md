# Ω-META-COMPUTE-PHYSICS-T∞ — R0.4

## Status

**Executable OAK-safe meta-discovery prototype.** R0.4 evolves the R0.1–R0.3 Complexity Atlas from measured resource modelling into a bounded system that can generate representations, inspect residual structure, maintain competing empirical theories, propose falsification measurements and seed cross-repository benchmark campaigns.

None of the following promotions are automatic:

- empirical fit → Big-O/Theta theorem;
- residual correlation → causal mechanism;
- static loop depth → runtime complexity proof;
- workload similarity → algorithmic equivalence;
- model disagreement → actual counterexample.

## Core loop

```text
repository/source
  -> static Repository Genome
  -> benchmark-priority seed
  -> measured ResourceSamples
  -> Representation Generator
  -> Theory Ecology
  -> held-out validation + uncertainty
  -> Residual Intelligence
  -> Hidden-Variable Candidates
  -> Self-Falsification measurements
  -> Meta-OAK
  -> Fleet Atlas / reusable workload families
  -> next measurement campaign
```

## 1. Representation Generator

`omega_compute_physics_t/representation.py`

The initial grammar is intentionally bounded and interpretable:

```text
x
log(x)
sqrt(x)
x*y
x/y
sqrt(x*y)
log(x/y)
```

Each derived coordinate is compared using held-out predictive error. The ranking objective is approximately:

```text
predictive compression - representation complexity penalty
```

A winning coordinate is stored as an `empirical-representation-candidate`; it is not declared fundamental or causal.

## 2. Residual Intelligence / Missing Variable Generator

`omega_compute_physics_t/residuals.py`

For observations

```text
r_i = y_i - y_hat_i
```

R0.4 searches numeric metadata and explicit auxiliary signals for associations with residuals. Strong associations become `MissingVariableCandidate` objects.

This implements the useful but conservative transition:

```text
structured model error
  -> candidate omitted state variable
  -> intervention / independent validation required
```

The engine never performs correlation → causality promotion.

## 3. Theory Ecology / Compute Theory Foundry

`omega_compute_physics_t/theory_foundry.py`

A theory candidate is:

```text
representation + validated finite-domain predictor + uncertainty evidence
```

The foundry keeps the original coordinate system and multiple generated coordinates alive simultaneously, ranking them by predictive error plus description cost.

No universal winner is assumed. Later releases can attach niches/regimes to theories.

## 4. Self-Falsification Candidate Generator

`rank_falsification_candidates(...)` searches points where surviving empirical theories disagree strongly.

```text
surviving theories
  -> candidate parameter points
  -> predictive disagreement
  -> high-value measurement candidates
```

A point becomes a true counterexample only after measurement contradicts a stated claim.

## 5. Meta-OAK

`omega_compute_physics_t/meta_oak.py`

Meta-OAK audits the validation machinery itself. R0.4 checks:

- finite predictive metrics;
- explicit calibration partition;
- calibration coverage;
- CV/train overfit ratio;
- representation improvement before promotion;
- causal-promotion block for residual associations;
- multiple-theory competition when available.

Passing Meta-OAK reduces known failure modes but is not a proof that unknown failure modes do not exist.

## 6. Universal Repository Genome Scanner

`omega_compute_physics_t/repo_scanner.py`

The scanner parses Python ASTs without executing repository code and extracts a `FunctionGenome` containing:

```text
LOC
argument count
loop count
maximum loop nesting
branches
calls
comprehensions
allocation hints
await/yield counts
direct recursion
async status
```

It also emits a structural scaling *candidate* such as:

```text
O(n^2) loop-depth candidate
```

This label means only that two statically visible loop levels were found. It explicitly omits iteration bounds, called-function costs, data dependence, compiler/runtime behaviour and hardware effects.

## 7. Benchmark Priority Compiler

`benchmark_priority(...)` ranks functions by transparent static measurement value:

```text
nested loops
+ loop count
+ branches
+ calls
+ LOC
+ recursion
+ async structure
```

This is not predicted runtime. It answers a different question:

> Which functions are most worth measuring first?

That distinction avoids spending benchmark budget uniformly across thousands of low-value functions.

## 8. Fleet Atlas — all repositories

`omega_compute_physics_t/fleet.py`

Multiple `RepositoryGenome` objects can be merged into one cross-repository Atlas:

```text
repo_1 -> genome_1 --\
repo_2 -> genome_2 ----> Fleet Atlas
repo_3 -> genome_3 --/
```

Each function receives a normalized static workload fingerprint. A deterministic similarity clustering creates `WorkloadFamily` objects.

This is the first executable seed of the proposed Workload Periodic Table / Complexity DNA concept.

The families are **static similarity families**, not empirical universality classes. Dynamic scaling measurements are required for that stronger promotion.

## 9. CLI

The meta CLI can be invoked without installing a new console-script entry point:

```bash
python -m omega_compute_physics_t.meta_cli scan . --output repo_genome.json
python -m omega_compute_physics_t.meta_cli represent samples.jsonl wall_time_s
python -m omega_compute_physics_t.meta_cli theories samples.jsonl wall_time_s
```

`scan` is the immediate bridge to every local checkout.

## 10. Rollout protocol for all Tristan repositories

The safe fleet rollout is deliberately staged.

### Stage A — zero-execution static scan

For every accessible repository:

```text
checkout pinned commit
-> meta_cli scan
-> repository_genome.json
-> top benchmark candidates
```

No untrusted project code is executed in this stage.

### Stage B — benchmark-contract generation

For high-priority functions only, generate a measurement contract containing:

```text
callable
input variables
domain
safe synthetic fixture strategy
resource limits
timeout
expected side effects
provenance
```

Functions requiring network, credentials, destructive I/O or external side effects remain quarantined until explicitly adapted.

### Stage C — controlled dynamic measurement

```text
safe function adapter
-> bounded ResourceSamples
-> R0.2 validation
-> R0.4 representation/theory competition
-> residual analysis
-> Meta-OAK
```

### Stage D — cross-repository reuse

```text
measured workload family A in repo X
-> prior for similar workload in repo Y
-> fewer experiments
-> held-out validation in repo Y
```

Transfer is a prior, never an automatic truth.

### Stage E — Complexity CI

Only after stable baselines exist:

```text
commit_old vs commit_new
-> Complexity Diff
-> scaling/constant/crossover changes
-> confidence-aware regression gate
```

## 11. Target fleet architecture

```text
GitHub repositories
   |
   v
Repository Genome Scanner
   |
   +--> Fleet Workload Atlas
   |       |
   |       +--> similarity families
   |       +--> benchmark priorities
   |       +--> reusable priors
   |
   v
Controlled Benchmark Harness
   |
   v
ResourceSamples
   |
   +--> Representation Generator
   +--> Theory Foundry
   +--> Residual Intelligence
   +--> Active Experiment Generator
   +--> Budget Compiler
   +--> Complexity Diff
   |
   v
Meta-OAK + M-
```

## 12. R0.5 frontier

The next promotion should concentrate on execution infrastructure rather than adding dozens of speculative modules:

1. `BenchmarkContract-T` — typed safe invocation contracts for arbitrary functions;
2. `Complexity-IR-T` — static operation/interdependency IR;
3. `MachineGenome-T` — measured machine calibration rather than declared specs;
4. DAG critical-path and memory-liveness composition;
5. dynamic workload-family calibration across multiple repositories;
6. benchmark artifact ingestion into Fleet Atlas;
7. cross-commit and cross-repository Complexity Diff;
8. uncertainty-of-uncertainty / Meta-OAK calibration campaigns.

## Canonical OAK law

```text
static structure -> hypothesis
measurement -> evidence
held-out validation -> finite-domain confidence
intervention -> causal evidence candidate
algorithmic analysis -> complexity argument
formal proof -> theorem
```

R0.4 never skips a rung in this ladder.
