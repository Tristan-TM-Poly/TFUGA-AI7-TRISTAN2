# Ω-GAME-SIM-EVO-T∞ / Ω-GENESIS-ENGINE-T∞

**Maturity:** R0.7 executable prototype  
**Host:** `omega_game_t`  
**Authority:** research / benchmark / review only

## Mother architecture

```text
GameSpec / generators
→ bounded compilation
→ WorldGraph + ArenaConfig + RuleKernel + agents + optional ArenaLayout
→ Simulate
→ Compete
→ Measure
→ Evolve / Coevolve
→ Quality Diversity
→ M+ / M- / Hall of Fame
→ OAK
→ next generation
```

The project advances through small falsifiable units:

```text
R0.1 deterministic experiment
→ R0.2 sparse/event execution
→ R0.3 quality diversity
→ R0.4 evolutionary memory
→ R0.5 agent↔environment coevolution
→ R0.6 bounded GameSpec compiler
→ R0.7 fixed hashed layouts
```

Ω-GAME-SIM-EVO-T∞ extends the merged Ω-GAME-T `WorldGraph` / `OAKGate` lineage; it does not replace it.

## R0.1–R0.6 retained

### R0.1 — deterministic substrate

Arena-T0 provides explicit seeds/configs/genomes, replay SHA-256 identity, mirrored tournaments, vector ratings, deterministic mutation/selection, WorldGraph projection, OAK audit and bounded fuzzing.

### R0.2 — sparse/event kernel

Dirty frontiers, scheduled events, Temporal LOD, dependency DAGs, bounded batches and deterministic work-unit accounting operationalize the target `cost ~ active frontier`.

### R0.3 — quality diversity

A deterministic MAP-Elites-style archive preserves strong but behaviorally distinct agents instead of collapsing search to a single scalar champion.

### R0.4 — evolutionary memory

Tournament champions become Hall-of-Fame/M+ evidence; fuzz failures become M- evidence; candidates are regressed against distinct historical champions to expose forgetting.

### R0.5 — agent↔environment coevolution

Bounded environment genomes compile to ArenaConfig, environments are evaluated on disjoint train/validation seeds, and agents receive explicit generalization-gap/worst-case receipts. Environments can evolve under a documented adversarial benchmark score.

### R0.6 — bounded GameSpec compiler

GameSpec 0.1 is an allow-listed declarative IR. It lowers agents, environment and rules into existing engine primitives, runs OAK before execution and emits deterministic build receipts. No arbitrary code/import/shell/callback surface is accepted.

## R0.7 — fixed hashed layout execution

### Why geometry becomes first-class

R0.5 evolves statistical environment parameters. R0.7 adds explicit geometry so two environments with equal dimensions and resource counts can still be distinguished by the actual arrangement of spawns, resources and obstacles.

The path is now:

```text
GameSpec.layout
→ ArenaLayout
→ structural validation
→ graph/geometric audit
→ layout_hash
→ Arena-T0
→ tournament
→ replay receipt
→ WorldGraph
```

A fixed layout is therefore executable state, not decorative metadata.

### ArenaLayout

The current bounded layout IR contains:

```text
width, height
left_spawn, right_spawn
resources[]
obstacles[]
```

Coordinates are integer grid pairs. Structural validation fails closed when:

- dimensions are smaller than 2;
- spawns coincide;
- any coordinate is out of bounds;
- resources or obstacles contain duplicates;
- a resource overlaps a spawn;
- an obstacle overlaps a spawn;
- a resource overlaps an obstacle.

Resources and obstacles are sorted before serialization so logically equivalent coordinate sets have one canonical representation.

### Layout identity

The layout receipt is:

```text
layout_hash = SHA256(canonical_json(normalized_layout))
```

The hash identifies exact normalized geometry. It does not establish fairness or quality.

```text
LAYOUT_HASH != FAIRNESS
LAYOUT_HASH != FUN
```

### Connectivity and reachability

R0.7 uses deterministic breadth-first search over four-neighbor grid connectivity while excluding obstacles.

`distance_map(layout, origin)` produces graph distance from an origin to every reachable cell.

The layout audit checks:

```text
left_spawn ↔ right_spawn reachable
∀ resource r:
  left_spawn ↔ r reachable
  right_spawn ↔ r reachable
```

Failure signals include:

```text
spawn_disconnected
resource_not_reachable_by_both
```

Connectivity means a path exists in this graph. It does not imply strategic balance.

```text
CONNECTED_LAYOUT != BALANCED_LAYOUT
```

### Geometric resource asymmetry

When resources exist and are reachable by both players, R0.7 computes mean shortest-path resource distance from each spawn:

```text
L = mean_r d(left_spawn, r)
R = mean_r d(right_spawn, r)
A = |L - R| / max(1, L, R)
```

The layout is flagged when:

```text
A > fairness_threshold
```

The threshold is explicit and configurable in `ArenaLayout.audit`, `audit_match`, and `GameSpecCompiler` policy surfaces.

This metric measures only one geometric asymmetry. It does not prove competitive fairness:

```text
DISTANCE_SYMMETRY != STRATEGIC_FAIRNESS
FAIRNESS_THRESHOLD != UNIVERSAL_FAIRNESS_DEFINITION
```

### Runtime validity vs compiler policy

R0.7 separates two responsibilities.

**Arena-T0 runtime** enforces structural validity and reachability. It uses a permissive asymmetry threshold so valid but asymmetric maps remain mechanically simulatable.

**GameSpecCompiler / OAK audit** may impose a stricter project fairness threshold. Thus an artifact can be structurally executable yet rejected for a benchmark or tournament policy.

```text
STRUCTURALLY_RUNNABLE != OAK_ACCEPTED_FOR_COMPETITION
```

### Obstacle-aware movement

With a fixed layout, movement toward resources or adversaries uses shortest-path candidates derived from BFS distance maps. Exploration is restricted to walkable neighbors.

Obstacles are also checked at action application time, so a proposed obstacle move returns `blocked` rather than changing state.

Without a layout, Arena-T0 retains the existing seeded random-resource / Manhattan-step behavior for backward compatibility.

### Replay provenance

R0.7 extends the match receipt payload with:

```text
normalized layout
layout_hash
```

Therefore changing only geometry changes replay identity even if seed, agents and ArenaConfig remain constant.

`audit_match` reruns the exact same layout when checking determinism.

### WorldGraph projection

For a fixed-layout match, `match_world_graph` adds:

```text
Entity(
  id = "layout:<hash-prefix>",
  kind = "arena_layout",
  traits = normalized_layout
)
```

This connects map geometry to the existing HGFM-compatible world/evidence representation.

### Tournament propagation

`run_round_robin(..., layout=layout)` passes the identical fixed layout to every mirrored match and seed. Every `MatchResult` therefore carries the same `layout_hash`, while stochastic choices remain controlled by match seeds.

### GameSpec integration

GameSpec 0.1 now accepts optional:

```text
layout: {
  width, height,
  left_spawn, right_spawn,
  resources, obstacles
}
```

Compiler gates include:

```text
environment dimensions == layout dimensions
layout structural validation
layout connectivity/reachability audit
configured geometric asymmetry threshold
resource_count := len(layout.resources)
```

The compiler build receipt includes both `layout_hash` and the exact `LayoutAudit` record.

### Action vocabulary repair

R0.6 exposed `idle` while Arena-T0 replay semantics used `stay`. R0.7 removes that representational mismatch:

```text
canonical runtime action = stay
legacy GameSpec alias: idle → stay
```

`ARENA_ACTIONS` now represents actual executable semantics:

```text
attack, harvest, move, stay
```

The schema still accepts `idle` for backward compatibility, but normalized GameSpec/build receipts contain `stay`.

### Fixed-layout example

```text
omega_game_t/examples/game_spec_fixed_layout.json
```

can be compiled and executed with:

```bash
cd omega_game_t
PYTHONPATH=. python -m omega_game compile-spec examples/game_spec_fixed_layout.json --seed 42 --tournament
```

## OAK boundary ledger

```text
LAYOUT_HASH != FAIRNESS
CONNECTED_LAYOUT != BALANCED_LAYOUT
DISTANCE_SYMMETRY != STRATEGIC_FAIRNESS
FIXED_LAYOUT != FUN_LEVEL
FAIRNESS_THRESHOLD != UNIVERSAL_FAIRNESS_DEFINITION
STRUCTURALLY_RUNNABLE != OAK_ACCEPTED_FOR_COMPETITION
COMPILED_SPEC != FUN_GAME
SCHEMA_VALID != SEMANTICALLY_GOOD
BUILD_RECEIPT != EXTERNAL_CERTIFICATION
OAK_ACCEPTED_BUILD != SCIENTIFIC_TRUTH
DETERMINISTIC_REPLAY != PHYSICAL_TRUTH
TOURNAMENT_WIN != GENERAL_INTELLIGENCE
WORK_UNIT_REDUCTION != WALL_CLOCK_SPEEDUP
QD_COVERAGE != BEHAVIORAL_COMPLETENESS
HALL_OF_FAME != GLOBAL_OPTIMALITY
M_PLUS != PROOF_OF_TRUTH
M_MINUS != PROOF_OF_IMPOSSIBILITY
HELD_OUT_SEEDS != REAL_WORLD_GENERALIZATION
ADVERSARIAL_SCORE != UNIVERSAL_DIFFICULTY
```

## Executable operating laws

```text
geometry as executable state, not decoration
canonicalize before hashing
validate connectivity before competition
separate runtime validity from fairness policy
keep aliases at the input boundary; hash canonical semantics
include environment identity in replay provenance
specification before code generation
allow-list before extensibility
OAK before execution
reproducibility before scale
mirrored competition before champion claims
active frontier before total-world scanning
ecology of elites before single-champion collapse
historical regression before declaring progress
held-out seeds before generalization claims
counterexamples before canonization
```

## R0.8+ roadmap

### R0.8 — adversarial layout evolution

- mutate resources/obstacles/spawns under bounded operators;
- connectivity-preserving repair/rejection;
- held-out map sets distinct from train maps;
- layout difficulty and discrimination receipts;
- map-generalization gaps;
- M- registry for invalid/unfair/dead layouts.

### R0.9 — scalable execution experiments

- sharding;
- checkpoints;
- backpressure;
- hardware profiler adapters;
- CPU/GPU scheduling experiments;
- empirical wall-clock/energy OAKBench.

### R0.10 — richer adapters

- TextWorld;
- Quest-CVCD;
- additional simulation domains;
- each behind explicit typed adapter contracts.

No compiled/generated game, map, evolved environment or benchmark champion is automatically considered fun, fair, safe, scientifically valid, generally intelligent or publishable.
