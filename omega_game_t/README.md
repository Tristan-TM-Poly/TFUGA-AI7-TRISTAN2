# Omega GAME T — Core Split

Issue: #90  
Status: small merge units split from the larger GAME branch.

## Ω-GAME-SIM-EVO-T∞ progression

### R0.1 — deterministic substrate — merged

Arena-T0, replay SHA-256, mirrored tournaments, vector ratings, deterministic selection/mutation, WorldGraph/OAK bridge and fuzzing.

### R0.2 — sparse/event kernel — merged

DirtyFrontier, ScheduledEvent, SparseEventScheduler, Temporal LOD, dependency DAG, bounded batches and deterministic CostGraph accounting.

### R0.3 — quality diversity — merged

BehaviorDescriptor, deterministic MAP-Elites, elite-per-cell retention, normalized novelty and QD/coverage metrics.

### R0.4 — evolutionary memory — merged

Hall of Fame receipts, explicit M+/M- stores, fuzz-failure retention and mirrored historical anti-forgetting regressions.

### R0.5 — agent ↔ environment coevolution — merged

Bounded environment genomes, train/held-out validation seeds, agent generalization receipts, adversarial environment ranking and deterministic environment evolution.

### R0.6 — bounded GameSpec compiler

R0.6 adds a declarative front door for the engine.

Implemented:

- `GameSpec` version `0.1`;
- strict rejection of unknown top-level/nested fields;
- `GameAgentSpec`, `GameEnvironmentSpec`, `GameRuleSpec`;
- bounded Arena-T0 action vocabulary: `attack`, `harvest`, `idle`, `move`;
- agent normalization through the existing `AgentGenome` contract;
- environment normalization through `EnvironmentGenome` → `ArenaConfig.validate()`;
- unique-agent and minimum-population gates;
- compilation to `WorldGraph + RuleKernel + ArenaConfig + AgentGenome[]`;
- OAK evaluation before execution;
- deterministic SHA-256 `build_receipt`;
- `CompiledGame.run_tournament()` blocked when OAK rejects the build;
- JSON Schema at `schemas/game_spec.schema.json`;
- example at `examples/game_spec_arena_t0.json`;
- `omega-game compile-spec` CLI.

Compiler law:

```text
JSON GameSpec
→ bounded parser
→ normalize
→ WorldGraph + RuleKernel + ArenaConfig + agents
→ OAK
→ deterministic build receipt
→ optional mirrored tournament
```

The compiler never imports arbitrary user modules or evaluates code from the spec.

### Headless CLI

```bash
cd omega_game_t
PYTHONPATH=. python -m omega_game arena --seed 42 --steps 96
PYTHONPATH=. python -m omega_game tournament --seed 42 --population 8 --steps 64
PYTHONPATH=. python -m omega_game evolve --seed 42 --population 8 --generations 3 --steps 48
PYTHONPATH=. python -m omega_game quality-diversity --seed 42 --population 16 --steps 48 --bins 8
PYTHONPATH=. python -m omega_game memory-demo --seed 42 --population 8 --top-k 3 --steps 32 --threshold 0.5
PYTHONPATH=. python -m omega_game coevolve --seed 42 --population 6 --environments 4 --adversarial-limit 2 --next-environments 4
PYTHONPATH=. python -m omega_game compile-spec examples/game_spec_arena_t0.json --seed 42 --tournament
PYTHONPATH=. python -m omega_game fuzz --seed 42 --cases 100
PYTHONPATH=. python -m omega_game sparse-bench --seed 42 --entities 10000 --active 100 --ticks 128
```

## OAK boundaries

```text
COMPILED_SPEC != FUN_GAME
COMPILED_SPEC != FAIR_GAME
BUILD_RECEIPT != EXTERNAL_CERTIFICATION
SCHEMA_VALID != SEMANTICALLY_GOOD
OAK_ACCEPTED_BUILD != SCIENTIFIC_TRUTH
DETERMINISTIC_REPLAY != PHYSICAL_TRUTH
TOURNAMENT_WIN != GENERAL_INTELLIGENCE
HELD_OUT_SEEDS != REAL_WORLD_GENERALIZATION
WORK_UNIT_REDUCTION != HARDWARE_SPEEDUP
```

## Local test

```bash
cd omega_game_t
python -m pytest
```

## Next split units

1. explicit fixed map layouts and connectivity/fairness gates;
2. GameSpec map/layout extension;
3. extinct-lineage registry and richer M- minimization;
4. TextWorld / Quest-CVCD adapters;
5. profiler-driven CPU/GPU scheduling experiments;
6. scheduler sharding/checkpoint/backpressure experiments.
