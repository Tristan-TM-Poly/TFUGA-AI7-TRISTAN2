# Omega GAME T — Core Split

Issue: #90  
Status: small merge units split from the larger GAME branch.

## Scope already merged

The first reviewable units established:

- graph primitives;
- event validation;
- quality scoring;
- OAK gate;
- tests and CI;
- LanguageGM engines, rubric, curriculum, validators, repair loop and dataset forge.

## Ω-GAME-SIM-EVO-T∞ R0.1 — merged

R0.1 reconnects the original GAME/world idea to an executable headless laboratory without reviving oversized PR #82.

Implemented:

- deterministic `Arena-T0` simulation;
- explicit `AgentGenome` and `ArenaConfig`;
- replay SHA-256 receipts;
- mirrored multi-seed round-robin tournaments;
- multidimensional ratings: performance, robustness, efficiency, novelty, stability;
- deterministic evolutionary selection/mutation;
- replay projection into the already-merged `WorldGraph`;
- OAK + deterministic replay audits;
- bounded fuzzing for invariant discovery.

## Ω-GAME-SIM-EVO-T∞ R0.2 — sparse/event kernel

R0.2 turns the optimization law `cost ~ active frontier` into executable scheduler primitives.

Implemented:

- `DirtyFrontier`: deduplicated deterministic active entity set;
- `ScheduledEvent`: explicit future event with tick/system/entity/payload;
- `SparseEventScheduler`: wake/sleep dispatch from dirty state and events;
- `TemporalSignal`: activity/importance/uncertainty/visibility signal;
- `TemporalLODPolicy`: realtime/active/background/dormant cadences;
- `SystemSpec.dependencies`: deterministic system dependency DAG;
- priority ordering among dependency-ready systems;
- fail-closed unknown dependency and cycle detection;
- bounded `max_batch` processing;
- `CostGraph`: deterministic work-unit accounting;
- `run_sparse_benchmark`: full-scan vs sparse algorithmic accounting.

The benchmark deliberately reports **work units**, not hardware speedup. For a baseline where each entity update costs one unit:

```text
naive work = total_entities × ticks
sparse work = processed_active_entities
reduction = 1 - sparse_work / naive_work
```

A low sparse-work count demonstrates reduced algorithmic work under the benchmark assumptions; it does not by itself prove lower wall-clock time, energy, cache misses or GPU cost.

### Headless CLI

```bash
cd omega_game_t
PYTHONPATH=. python -m omega_game arena --seed 42 --steps 96
PYTHONPATH=. python -m omega_game tournament --seed 42 --population 8 --steps 64
PYTHONPATH=. python -m omega_game evolve --seed 42 --population 8 --generations 3 --steps 48
PYTHONPATH=. python -m omega_game fuzz --seed 42 --cases 100
PYTHONPATH=. python -m omega_game sparse-bench --seed 42 --entities 10000 --active 100 --ticks 128
```

Theory and evidence boundaries: `docs/theories/OMEGA_GAME_SIM_EVO_T_INFINITY.md`.

## Boundary

Omega GAME T is a game, simulation, and research lab. It is not a tool for manipulation, unfair automation, unsafe real-world instructions, or external certification.

Deterministic simulation is a reproducibility property, not evidence that a simulated law is physically true. Tournament performance is benchmark evidence, not a claim of general intelligence. Scheduler work-unit reduction is an algorithmic accounting result, not a hardware performance claim.

## Local test

```bash
cd omega_game_t
python -m pytest
```

## Next split units

1. quality-diversity archive / MAP-Elites;
2. Hall of Fame and M- counterexample memory;
3. agent ↔ map coevolution;
4. adversarial level generation and hidden challenge seeds;
5. GameSpec compiler;
6. TextWorld / Quest-CVCD adapters;
7. profiler-driven CPU/GPU scheduling experiments;
8. scheduler sharding/checkpoint/backpressure experiments.
