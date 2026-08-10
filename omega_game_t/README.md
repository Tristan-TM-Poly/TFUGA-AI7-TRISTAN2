# Omega GAME T — Ω-GAME-SIM-EVO-T∞

Status: **R1.0.6 local executable research package candidate**.  
Authority: simulation / benchmark / provenance / OAK review only.

Omega GAME T is a deterministic research laboratory for generated games and algorithmic worlds. Development is split into small tested layers and consolidated through executable OAK gates rather than promoted from architecture alone.

## Executable ladder

```text
R0.1  deterministic Arena-T0 / tournaments / evolution / replay audit
R0.2  sparse-event scheduling / Temporal LOD / CostGraph
R0.3  MAP-Elites quality diversity
R0.4  Hall of Fame + M+ / M- + anti-forgetting
R0.5  agent↔environment coevolution + held-out seeds
R0.6  bounded GameSpec compiler
R0.7  fixed hashed layouts + geometry gates
R0.8  adversarial layout evolution + held-out maps
R0.9  deterministic sharded campaigns + checkpoints
R0.10 local persisted/process runtime
R0.11 portable campaign bundles + heartbeat/TTL + local CAS
R0.12 causal coordinator ledger + replay audit
R0.13 ExperimentGraph + selection evidence closure
R1.0  integrated OAKBench + fault matrix + capability report
R1.0.1 checkpoint round-trip + retry/replay hardening
R1.0.2 public integrated OAKBench API + CLI
R1.0.3 installable Python package + console-entry CI
R1.0.4 CPython 3.11–3.13 CI matrix + isolated wheel/OAKBench smoke
R1.0.5 deterministic-vs-empirical ScaleBench
R1.0.6 retained CI ScaleBench observations per commit
```

## Install

```bash
cd omega_game_t
python -m pip install -e .
omega-game --help
```

Python requirement: **3.11+**. CI explicitly exercises CPython 3.11, 3.12 and 3.13.

## Integrated OAKBench

```bash
omega-game oakbench
```

The integrated path spans GameSpec, fixed layout, deterministic Arena-T0, replay audit, held-out maps, sharded campaign, checkpoint, bundle/local CAS, coordinator ledger, ExperimentGraph, evidence-backed selection, process equivalence and fault injection.

The current fault matrix exercises replay tamper, disconnected layouts, checkpoint/bundle/CAS tamper, coordinator-event tamper, missing selection evidence, held-out-map leakage and wrong-worker acknowledgement.

## ScaleBench

Run the bounded matrix:

```bash
omega-game scale-bench --matrix --seed 1901
```

or one explicit scenario:

```bash
omega-game scale-bench --seed 1801 --population 6 --seed-count 2 --max-steps 8 --shards 3 --repetitions 2 --workers 2
```

ScaleBench hashes deterministic workload identity, work units and checkpoint/benchmark receipts. It reports wall-clock, `tracemalloc` and observed process speedup separately; those empirical fields are not part of deterministic provenance.

## CI observability

GitHub Actions runs five validation surfaces:

```text
CPython 3.11 full suite
CPython 3.12 full suite
CPython 3.13 full suite
isolated wheel + integrated OAKBench
ScaleBench observation + artifact upload
```

The final job uploads `omega-game-scale-observation-<commit-sha>` containing `scale-observation.json` with 30-day retention. This is an empirical observation ledger, not a canonical performance truth ledger.

## Public Python API

```python
from omega_game import IntegratedOAKBenchConfig, run_integrated_oakbench

report = run_integrated_oakbench(IntegratedOAKBenchConfig(seed=1401, process_workers=2))
assert report.accepted
```

## Evidence boundaries

```text
DETERMINISTIC_REPLAY != PHYSICAL_TRUTH
TOURNAMENT_WIN != GENERAL_INTELLIGENCE
WORK_UNITS != CPU_CYCLES
RUNNER_TIME != DETERMINISTIC_RECEIPT
TRACEMALLOC_PEAK != TOTAL_PROCESS_MEMORY
OBSERVED_SPEEDUP != GUARANTEED_SPEEDUP
HELD_OUT_SEEDS/MAPS != REAL_WORLD_GENERALIZATION
GEOMETRIC_SYMMETRY != STRATEGIC_FAIRNESS
TTL_LEASE_COORDINATOR != DISTRIBUTED_CONSENSUS
LOCAL_CAS != REMOTE_DURABILITY
EVENT_CHAIN_INTEGRITY != EXTERNAL_EVENT_TRUTH
PROVENANCE_CLOSURE != LOGICAL_PROOF
INTEGRATED_PASS != SCIENTIFIC_TRUTH
CI_ARTIFACT != CANONICAL_PROOF
```

The capability report intentionally keeps distributed consensus, remote durable storage, guaranteed process speedup, strategic fairness, fun and general intelligence as **not demonstrated**.

## Key theory notes

- `docs/theories/OMEGA_GAME_R100_INTEGRATED_OAKBENCH.md`
- `docs/theories/OMEGA_GAME_SCALEBENCH_R105.md`
- `docs/theories/OMEGA_GAME_CI_OBSERVABILITY_R106.md`

## Next OAK work

Accumulate repeated comparable ScaleBench observations before introducing statistical performance-regression bands. Then extend fault/property campaigns and version-migration tests before considering remote coordination/storage adapters.
