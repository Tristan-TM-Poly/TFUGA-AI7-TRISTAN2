# Omega GAME T — Core Split

Issue: #90  
Status: small merge units split from the larger GAME branch.

## Ω-GAME-SIM-EVO-T∞ progression

- **R0.1 merged:** deterministic Arena-T0, replay SHA-256, tournaments/evolution/OAK/fuzzing.
- **R0.2 merged:** DirtyFrontier, event scheduler, Temporal LOD, dependency DAG, CostGraph.
- **R0.3 merged:** deterministic MAP-Elites quality diversity.
- **R0.4 merged:** Hall of Fame, M+/M-, anti-forgetting regression.
- **R0.5 merged:** agent↔environment coevolution with held-out seeds.
- **R0.6 merged:** bounded GameSpec compiler and deterministic build receipts.

### R0.7 — fixed hashed layouts

R0.7 makes map geometry executable rather than decorative metadata.

Implemented:

- immutable `ArenaLayout(width, height, left_spawn, right_spawn, resources, obstacles)`;
- canonical sorting + SHA-256 `layout_hash`;
- bounds/uniqueness/no-overlap validation;
- BFS connectivity and distance maps;
- bilateral resource-reachability gate;
- configurable resource-distance asymmetry policy;
- obstacle-aware shortest-path movement;
- fixed spawns/resources/obstacles consumed by Arena-T0;
- layout identity in replay receipts and deterministic reruns;
- `arena_layout` entity in WorldGraph projection;
- `run_round_robin(..., layout=...)` propagation;
- explicit `layout_fairness_threshold` in audits/compiler;
- optional GameSpec `layout` lowering;
- GameSpec environment/layout dimension consistency;
- compiler derives `resource_count` from fixed resources;
- layout audit/hash inside build receipt;
- canonical runtime action `stay`, with legacy input alias `idle → stay`;
- schema + `examples/game_spec_fixed_layout.json`;
- backward compatibility: matches/specs without a layout keep their previous serialized surface and replay hash contract.

```text
GameSpec.layout
→ ArenaLayout
→ structural validation
→ connectivity/reachability
→ fairness-policy audit
→ layout_hash
→ Arena-T0
→ tournament / replay / WorldGraph
```

Example:

```bash
cd omega_game_t
PYTHONPATH=. python -m omega_game compile-spec examples/game_spec_fixed_layout.json --seed 42 --tournament
```

## OAK boundaries

```text
LAYOUT_HASH != FAIRNESS
CONNECTED_LAYOUT != BALANCED_LAYOUT
DISTANCE_SYMMETRY != STRATEGIC_FAIRNESS
FIXED_LAYOUT != FUN_LEVEL
FAIRNESS_THRESHOLD != UNIVERSAL_FAIRNESS_DEFINITION
STRUCTURALLY_RUNNABLE != OAK_ACCEPTED_FOR_COMPETITION
BUILD_RECEIPT != EXTERNAL_CERTIFICATION
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

1. adversarial fixed-layout mutation/evolution with connectivity-preserving repair/rejection;
2. train/validation layout sets and map-generalization receipts;
3. extinct-lineage registry and richer M- minimization;
4. TextWorld / Quest-CVCD adapters;
5. profiler-driven CPU/GPU scheduling experiments;
6. scheduler sharding/checkpoint/backpressure experiments.
