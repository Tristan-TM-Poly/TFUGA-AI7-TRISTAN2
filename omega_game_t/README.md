# Omega GAME T — Ω-GAME-SIM-EVO-T∞

Status: **R1.0.3 local executable research package candidate**.  
Authority: simulation / benchmark / provenance / OAK review only.

Omega GAME T is a deterministic research laboratory for generated games and algorithmic worlds. Development is intentionally split into small tested layers and consolidated through an integrated OAKBench rather than promoted from architecture alone.

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
```

## Install for development

From the repository root:

```bash
cd omega_game_t
python -m pip install -e .
```

The package installs the console command:

```bash
omega-game --help
```

Python requirement: **3.11+**.

## Integrated OAKBench

The main consolidation gate can be launched directly:

```bash
omega-game oakbench
```

Example with explicit controls:

```bash
omega-game oakbench \
  --seed 1401 \
  --max-steps 8 \
  --layouts 3 \
  --shards 2 \
  --workers 2 \
  --fairness-threshold 0.5
```

The integrated path is:

```text
GameSpec
→ fixed ArenaLayout
→ deterministic Arena-T0
→ replay/audit
→ held-out map generalization
→ sharded campaign
→ checkpoint
→ bundle + local CAS restore
→ causal coordinator ledger
→ ExperimentGraph + M+/M-
→ evidence-backed selection decision
→ process equivalence
→ fault injection
→ capability report
```

The command exits non-zero when the integrated report is not accepted.

### Fault matrix currently exercised

- replay SHA tamper;
- disconnected layout;
- checkpoint-result tamper;
- bundle-manifest tamper;
- local CAS corruption;
- coordinator-event tamper;
- selection decision with missing evidence;
- train/validation layout leakage;
- acknowledgement by a non-owning worker.

A detected fault means the named detector rejected that perturbation. It does **not** prove all fault classes are covered.

## Other CLI surfaces

```bash
omega-game arena --seed 42 --steps 96
omega-game tournament --seed 42 --population 8 --steps 64
omega-game evolve --seed 42 --population 8 --generations 3 --steps 48
omega-game quality-diversity --seed 42 --population 16 --steps 48 --bins 8
omega-game memory-demo --seed 42 --population 8 --top-k 3 --steps 32 --threshold 0.5
omega-game coevolve --seed 42 --population 6 --environments 4
omega-game compile-spec examples/game_spec_fixed_layout.json --seed 42 --tournament
omega-game fuzz --seed 42 --cases 100
omega-game sparse-bench --seed 42 --entities 10000 --active 100 --ticks 128
```

## Public Python OAKBench API

```python
from omega_game import IntegratedOAKBenchConfig, run_integrated_oakbench

report = run_integrated_oakbench(
    IntegratedOAKBenchConfig(seed=1401, process_workers=2)
)
assert report.accepted
```

## Evidence boundaries

The following distinctions are contractual:

```text
DETERMINISTIC_REPLAY != PHYSICAL_TRUTH
TOURNAMENT_WIN != GENERAL_INTELLIGENCE
WORK_UNIT_REDUCTION != WALL_CLOCK_SPEEDUP
QD_COVERAGE != BEHAVIORAL_COMPLETENESS
M_PLUS != PROOF_OF_TRUTH
M_MINUS != PROOF_OF_IMPOSSIBILITY
HELD_OUT_SEEDS/MAPS != REAL_WORLD_GENERALIZATION
LAYOUT_HASH != FAIRNESS
GEOMETRIC_SYMMETRY != STRATEGIC_FAIRNESS
LOCAL_PROCESS_EQUIVALENCE != GUARANTEED_SPEEDUP
TTL_LEASE_COORDINATOR != DISTRIBUTED_CONSENSUS
LOCAL_CAS != REMOTE_DURABILITY
EVENT_CHAIN_INTEGRITY != EXTERNAL_EVENT_TRUTH
PROVENANCE_CLOSURE != LOGICAL_PROOF
INTEGRATED_PASS != SCIENTIFIC_TRUTH
```

The capability report intentionally marks as **not demonstrated**: distributed consensus, remote durable artifact storage, guaranteed multi-process speedup, strategic fairness, fun, and general intelligence.

## CI / local validation

GitHub Actions installs the package itself, verifies the `omega-game` console entry point, then runs the complete test suite:

```bash
cd omega_game_t
python -m pip install -e .
omega-game --help
python -m pytest tests -q
```

## Provenance and theory notes

Key consolidation documents:

- `docs/theories/OMEGA_GAME_SIM_EVO_T_INFINITY.md`
- `docs/theories/OMEGA_GAME_CAMPAIGN_RUNTIME_R10.md`
- `docs/theories/OMEGA_GAME_CAMPAIGN_BUNDLES_R11.md`
- `docs/theories/OMEGA_GAME_COORDINATOR_LEDGER_R12.md`
- `docs/theories/OMEGA_GAME_EXPERIMENT_GRAPH_R13.md`
- `docs/theories/OMEGA_GAME_R100_INTEGRATED_OAKBENCH.md`

## Next OAK work

Priority is **hardening and empirical measurement**, not another abstraction layer:

1. larger deterministic/fault campaigns;
2. profiler-driven CPU/process experiments;
3. memory and checkpoint scale tests;
4. more mutation/property-based fault generation;
5. artifact/receipt migration tests across package versions;
6. only then evaluate real remote coordination/storage adapters if an actual backend is available.
