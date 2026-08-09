# Omega GAME T — Core Split

Issue: #90  
Status: small merge units split from the larger GAME branch.

## Scope already merged

The first reviewable units established graph/event primitives, quality scoring, OAK, tests/CI and the LanguageGM family.

## Ω-GAME-SIM-EVO-T∞ R0.1 — merged

R0.1 provides the deterministic experimental substrate:

- `Arena-T0` headless simulation;
- explicit `AgentGenome` / `ArenaConfig`;
- replay SHA-256 receipts;
- mirrored multi-seed tournaments;
- vector ratings;
- deterministic selection/mutation;
- replay → `WorldGraph` projection;
- OAK/determinism audits and fuzzing.

## Ω-GAME-SIM-EVO-T∞ R0.2 — merged

R0.2 turns `cost ~ active frontier` into executable scheduling:

- `DirtyFrontier`;
- future `ScheduledEvent`s;
- `SparseEventScheduler` wake/sleep dispatch;
- activity/importance/uncertainty/visibility Temporal LOD;
- dependency DAG + deterministic priority ordering;
- bounded batches;
- `CostGraph` work-unit accounting;
- full-scan vs sparse accounting benchmark.

`WORK_UNIT_REDUCTION != WALL_CLOCK_SPEEDUP` remains an explicit OAK boundary.

## Ω-GAME-SIM-EVO-T∞ R0.3 — quality diversity

R0.3 stops treating evolution as a search for only one champion.

Implemented:

- `ArchiveConfig` with selectable bounded genome axes;
- `BehaviorDescriptor`;
- deterministic multidimensional cell quantization;
- `MapElitesArchive`;
- one best elite per behavior cell;
- deterministic tie-breaks;
- normalized k-nearest archive novelty;
- `quality_from_rating` using tournament evidence;
- coverage, QD score, mean/max quality and mean novelty;
- `QualityDiversityExperiment` coupling tournament → archive;
- `quality-diversity` CLI command.

Default descriptor space:

```text
(aggression, exploration)
```

with configurable bin counts. The axes are a modeling choice, not a claim that they exhaust behavior.

### Headless CLI

```bash
cd omega_game_t
PYTHONPATH=. python -m omega_game arena --seed 42 --steps 96
PYTHONPATH=. python -m omega_game tournament --seed 42 --population 8 --steps 64
PYTHONPATH=. python -m omega_game evolve --seed 42 --population 8 --generations 3 --steps 48
PYTHONPATH=. python -m omega_game quality-diversity --seed 42 --population 16 --steps 48 --bins 8
PYTHONPATH=. python -m omega_game fuzz --seed 42 --cases 100
PYTHONPATH=. python -m omega_game sparse-bench --seed 42 --entities 10000 --active 100 --ticks 128
```

Theory and evidence boundaries: `docs/theories/OMEGA_GAME_SIM_EVO_T_INFINITY.md`.

## Boundary

Omega GAME T is a game, simulation, and research lab. It is not a tool for manipulation, unfair automation, unsafe real-world instructions, or external certification.

```text
DETERMINISTIC_REPLAY != PHYSICAL_TRUTH
TOURNAMENT_WIN != GENERAL_INTELLIGENCE
QD_COVERAGE != BEHAVIORAL_COMPLETENESS
NOVELTY != USEFULNESS
WORK_UNIT_REDUCTION != HARDWARE_SPEEDUP
```

## Local test

```bash
cd omega_game_t
python -m pytest
```

## Next split units

1. Hall of Fame + M+/M- evolutionary memory;
2. regression challenge sets from champions and failures;
3. agent ↔ map coevolution;
4. adversarial level generation + hidden seeds;
5. GameSpec compiler;
6. TextWorld / Quest-CVCD adapters;
7. profiler-driven CPU/GPU scheduling experiments;
8. scheduler sharding/checkpoint/backpressure experiments.
