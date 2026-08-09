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

### R0.5 — agent ↔ environment coevolution

R0.5 makes the benchmark environment evolvable without changing Arena-T0's simulation code.

Implemented:

- `EnvironmentGenome` with bounded world/rule parameters;
- deterministic `seed_environments`;
- genome → validated `ArenaConfig` compilation;
- train-seed tournament per environment;
- strictly held-out validation-seed tournament per environment;
- `EnvironmentEvaluation` with train/validation efficiency and difficulty;
- validation discrimination across agent qualities;
- `AgentGeneralization` with train mean, validation mean, gap, worst-case quality and validation standard deviation;
- deterministic evidence/coevolution receipt hashes;
- adversarial environment ranking;
- `evolve_environments` with elite retention + bounded deterministic mutation;
- `omega-game coevolve` CLI.

Current benchmark difficulty is:

```text
difficulty = 1 / (1 + mean_efficiency)
adversarial_score = validation_difficulty + 0.10 * validation_discrimination
```

These are explicit benchmark metrics, not universal definitions of difficulty or game quality.

### Headless CLI

```bash
cd omega_game_t
PYTHONPATH=. python -m omega_game arena --seed 42 --steps 96
PYTHONPATH=. python -m omega_game tournament --seed 42 --population 8 --steps 64
PYTHONPATH=. python -m omega_game evolve --seed 42 --population 8 --generations 3 --steps 48
PYTHONPATH=. python -m omega_game quality-diversity --seed 42 --population 16 --steps 48 --bins 8
PYTHONPATH=. python -m omega_game memory-demo --seed 42 --population 8 --top-k 3 --steps 32 --threshold 0.5
PYTHONPATH=. python -m omega_game coevolve --seed 42 --population 6 --environments 4 --adversarial-limit 2 --next-environments 4
PYTHONPATH=. python -m omega_game fuzz --seed 42 --cases 100
PYTHONPATH=. python -m omega_game sparse-bench --seed 42 --entities 10000 --active 100 --ticks 128
```

## OAK boundaries

```text
DETERMINISTIC_REPLAY != PHYSICAL_TRUTH
TOURNAMENT_WIN != GENERAL_INTELLIGENCE
QD_COVERAGE != BEHAVIORAL_COMPLETENESS
NOVELTY != USEFULNESS
HALL_OF_FAME != GLOBAL_OPTIMALITY
M_PLUS != PROOF_OF_TRUTH
M_MINUS != PROOF_OF_IMPOSSIBILITY
HELD_OUT_SEEDS != REAL_WORLD_GENERALIZATION
ADVERSARIAL_SCORE != UNIVERSAL_DIFFICULTY
ENVIRONMENT_GENOME != COMPLETE_LEVEL_DESCRIPTION
WORK_UNIT_REDUCTION != HARDWARE_SPEEDUP
```

## Local test

```bash
cd omega_game_t
python -m pytest
```

## Next split units

1. GameSpec compiler / schema;
2. adversarial fixed-map layouts rather than parameter-only environments;
3. extinct-lineage registry and richer M- minimization;
4. TextWorld / Quest-CVCD adapters;
5. profiler-driven CPU/GPU scheduling experiments;
6. scheduler sharding/checkpoint/backpressure experiments.
