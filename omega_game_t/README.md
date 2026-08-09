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

### R0.6 — bounded GameSpec compiler — merged
Strict allow-list GameSpec IR/schema, WorldGraph/RuleKernel/ArenaConfig lowering, OAK-before-execution and deterministic build receipts.

### R0.7 — fixed hashed layouts

R0.7 makes map geometry an executable part of Arena-T0 rather than decorative metadata.

Implemented:

- immutable `ArenaLayout` with dimensions, left/right spawns, resources and obstacles;
- canonical sorting + SHA-256 `layout_hash`;
- structural gates for bounds, uniqueness and overlap;
- BFS `distance_map` and obstacle-aware shortest-step candidates;
- spawn-connectivity audit;
- requirement that every resource be reachable by both spawns;
- configurable mean-resource-distance asymmetry gate;
- fixed spawns/resources/obstacles consumed directly by `run_arena_t0`;
- obstacle-aware movement and pathfinding;
- layout identity included in match replay receipts;
- deterministic reruns preserve the same layout;
- `WorldGraph` gains an `arena_layout` entity when a match has fixed geometry;
- `run_round_robin(..., layout=...)` propagates one fixed layout to every match;
- `audit_match(..., layout_fairness_threshold=...)` makes geometry policy explicit;
- GameSpec accepts optional fixed `layout` and derives `resource_count` from it;
- compiler rejects environment/layout dimension mismatches;
- compiler folds layout-audit flags into OAK acceptance;
- GameSpec build receipts contain layout hash + audit;
- runtime action vocabulary canonicalized to `stay`; legacy GameSpec input `idle` is retained as alias `idle → stay`;
- schema extended with fixed-layout coordinates;
- example `examples/game_spec_fixed_layout.json`;
- focused geometry/simulation/compiler tests.

Core geometry path:

```text
GameSpec.layout
→ ArenaLayout
→ structural validation
→ BFS connectivity/resource reachability
→ fairness-policy audit
→ layout_hash
→ Arena-T0 / Tournament / Replay / WorldGraph
```

Example:

```bash
cd omega_game_t
PYTHONPATH=. python -m omega_game compile-spec examples/game_spec_fixed_layout.json --seed 42 --tournament
```

The previous random-resource Arena-T0 path remains available when no layout is supplied.

## OAK boundaries

```text
LAYOUT_HASH != FAIRNESS
CONNECTED_LAYOUT != BALANCED_LAYOUT
DISTANCE_SYMMETRY != STRATEGIC_FAIRNESS
FIXED_LAYOUT != FUN_LEVEL
FAIRNESS_THRESHOLD != UNIVERSAL_FAIRNESS_DEFINITION
COMPILED_SPEC != FUN_GAME
BUILD_RECEIPT != EXTERNAL_CERTIFICATION
DETERMINISTIC_REPLAY != PHYSICAL_TRUTH
TOURNAMENT_WIN != GENERAL_INTELLIGENCE
HELD_OUT_SEEDS != REAL_WORLD_GENERALIZATION
WORK_UNIT_REDUCTION != HARDWARE_SPEEDUP
```

`ArenaLayout.audit` measures only documented graph/geometric properties. It does not infer strategic balance, accessibility for every policy, player enjoyment, or competitive fairness from geometry alone.

## Headless CLI

```bash
cd omega_game_t
PYTHONPATH=. python -m omega_game arena --seed 42 --steps 96
PYTHONPATH=. python -m omega_game tournament --seed 42 --population 8 --steps 64
PYTHONPATH=. python -m omega_game evolve --seed 42 --population 8 --generations 3 --steps 48
PYTHONPATH=. python -m omega_game quality-diversity --seed 42 --population 16 --steps 48 --bins 8
PYTHONPATH=. python -m omega_game memory-demo --seed 42 --population 8 --top-k 3 --steps 32 --threshold 0.5
PYTHONPATH=. python -m omega_game coevolve --seed 42 --population 6 --environments 4 --adversarial-limit 2 --next-environments 4
PYTHONPATH=. python -m omega_game compile-spec examples/game_spec_arena_t0.json --seed 42 --tournament
PYTHONPATH=. python -m omega_game compile-spec examples/game_spec_fixed_layout.json --seed 42 --tournament
PYTHONPATH=. python -m omega_game fuzz --seed 42 --cases 100
PYTHONPATH=. python -m omega_game sparse-bench --seed 42 --entities 10000 --active 100 --ticks 128
```

## Local test

```bash
cd omega_game_t
python -m pytest
```

## Next split units

1. adversarial fixed-layout mutation/evolution with connectivity-preserving repair;
2. train/validation layout sets and map-generalization receipts;
3. extinct-lineage registry and richer M- minimization;
4. TextWorld / Quest-CVCD adapters;
5. profiler-driven CPU/GPU scheduling experiments;
6. scheduler sharding/checkpoint/backpressure experiments.
