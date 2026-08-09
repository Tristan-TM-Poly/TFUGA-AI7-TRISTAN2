# Omega GAME T — Core Split

Issue: #90  
Status: small merge units split from the larger GAME branch.

## Ω-GAME-SIM-EVO-T∞ progression

### R0.1 — deterministic substrate — merged

- Arena-T0 headless simulation;
- replay SHA-256 receipts;
- mirrored tournaments + vector ratings;
- deterministic selection/mutation;
- WorldGraph/OAK bridge and fuzzing.

### R0.2 — sparse/event kernel — merged

- DirtyFrontier + ScheduledEvent;
- SparseEventScheduler;
- Temporal LOD;
- dependency DAG;
- bounded batches;
- deterministic CostGraph work accounting.

### R0.3 — quality diversity — merged

- BehaviorDescriptor;
- deterministic MAP-Elites archive;
- one elite per behavior cell;
- k-nearest novelty;
- coverage / QD score / quality metrics;
- tournament → archive pipeline.

### R0.4 — evolutionary memory

R0.4 makes historical evidence first-class instead of allowing each generation to overwrite its past.

Implemented:

- `ChampionRecord` with deterministic receipt hash;
- `HallOfFame` populated from tournament rankings;
- explicit `MemoryRecord` polarity: `plus` or `minus`;
- `EvolutionaryMemory` with deduplicated M⁺ and M⁻ stores;
- tournament champions automatically becoming M⁺ evidence;
- fuzz failures ingesting into M⁻ with campaign/case seeds and flags;
- manual M⁺/M⁻ records for future adapters;
- Hall-of-Fame challenge-agent extraction;
- `evaluate_anti_forgetting` regression tournaments;
- mirrored candidate-vs-historical-champion matches;
- configurable anti-forgetting threshold;
- deterministic `AntiForgettingReport`.

The anti-forgetting score is:

```text
score_fraction = candidate_points / available_points
passed = score_fraction >= configured_threshold
```

The threshold is a project benchmark policy, not a universal definition of progress.

### Headless CLI

```bash
cd omega_game_t
PYTHONPATH=. python -m omega_game arena --seed 42 --steps 96
PYTHONPATH=. python -m omega_game tournament --seed 42 --population 8 --steps 64
PYTHONPATH=. python -m omega_game evolve --seed 42 --population 8 --generations 3 --steps 48
PYTHONPATH=. python -m omega_game quality-diversity --seed 42 --population 16 --steps 48 --bins 8
PYTHONPATH=. python -m omega_game memory-demo --seed 42 --population 8 --top-k 3 --steps 32 --threshold 0.5
PYTHONPATH=. python -m omega_game fuzz --seed 42 --cases 100
PYTHONPATH=. python -m omega_game sparse-bench --seed 42 --entities 10000 --active 100 --ticks 128
```

Theory and evidence boundaries: `docs/theories/OMEGA_GAME_SIM_EVO_T_INFINITY.md`.

## OAK boundaries

```text
DETERMINISTIC_REPLAY != PHYSICAL_TRUTH
TOURNAMENT_WIN != GENERAL_INTELLIGENCE
QD_COVERAGE != BEHAVIORAL_COMPLETENESS
NOVELTY != USEFULNESS
HALL_OF_FAME != GLOBAL_OPTIMALITY
M_PLUS != PROOF_OF_TRUTH
M_MINUS != PROOF_OF_IMPOSSIBILITY
ANTI_FORGETTING_THRESHOLD != UNIVERSAL_PROGRESS_CRITERION
WORK_UNIT_REDUCTION != HARDWARE_SPEEDUP
```

## Local test

```bash
cd omega_game_t
python -m pytest
```

## Next split units

1. agent ↔ map coevolution;
2. adversarial map generation + hidden validation seeds;
3. extinct-lineage registry and richer M- minimization;
4. GameSpec compiler;
5. TextWorld / Quest-CVCD adapters;
6. profiler-driven CPU/GPU scheduling experiments;
7. scheduler sharding/checkpoint/backpressure experiments.
