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

Progression:

```text
R0.1 deterministic experiment
→ R0.2 sparse/event execution
→ R0.3 quality diversity
→ R0.4 evolutionary memory
→ R0.5 agent↔environment coevolution
→ R0.6 bounded GameSpec compiler
→ R0.7 fixed hashed layouts
```

## R0.1–R0.6 retained

R0.1 established deterministic Arena-T0, replay receipts, tournaments, evolution, WorldGraph/OAK and fuzzing. R0.2 added sparse/event scheduling and work-unit accounting. R0.3 added deterministic MAP-Elites. R0.4 added Hall of Fame plus M+/M- anti-forgetting memory. R0.5 added environment coevolution with disjoint train/validation seeds. R0.6 added the bounded GameSpec IR/compiler and OAK-before-execution.

## R0.7 — geometry as executable state

R0.7 distinguishes two worlds that have identical dimensions and resource counts but different actual geometry.

### ArenaLayout IR

```text
ArenaLayout = (
  width, height,
  left_spawn, right_spawn,
  resources[], obstacles[]
)
```

Validation fails closed for out-of-bounds coordinates, duplicate resources/obstacles, coincident spawns, spawn/resource overlap, spawn/obstacle overlap and resource/obstacle overlap.

Resources and obstacles are sorted before canonical serialization.

### Canonical layout identity

```text
layout_hash = SHA256(canonical_json(normalized_layout))
```

The hash identifies exact normalized geometry only.

```text
LAYOUT_HASH != FAIRNESS
LAYOUT_HASH != FUN
```

### Connectivity and resource reachability

Four-neighbor BFS computes deterministic graph distance while excluding obstacles.

A layout audit checks:

```text
left_spawn ↔ right_spawn
∀ resource r:
    left_spawn ↔ r
    right_spawn ↔ r
```

Signals:

```text
spawn_disconnected
resource_not_reachable_by_both
```

Connectivity is necessary for this benchmark but is not strategic balance.

### Geometric asymmetry

For reachable resources:

```text
L = mean_r d(left_spawn, r)
R = mean_r d(right_spawn, r)
A = |L - R| / max(1, L, R)
```

The policy may flag a layout when `A > fairness_threshold`.

```text
DISTANCE_SYMMETRY != STRATEGIC_FAIRNESS
FAIRNESS_THRESHOLD != UNIVERSAL_FAIRNESS_DEFINITION
```

### Runtime validity vs benchmark policy

Arena-T0 enforces structural validity and reachability. Compiler/audit layers may impose stricter geometric asymmetry thresholds.

```text
STRUCTURALLY_RUNNABLE != OAK_ACCEPTED_FOR_COMPETITION
```

This separation prevents runtime mechanics from silently hard-coding one universal fairness policy.

### Obstacle-aware movement

Fixed-layout movement toward a target uses shortest-path candidates. Exploration uses walkable neighbors. Action application independently rejects obstacle moves as `blocked`.

Without a layout, Arena-T0 keeps the R0.1–R0.6 seeded random-resource behavior.

### Backward-compatible replay identity

A critical R0.7 rule is:

```text
NO_LAYOUT → preserve legacy serialized surface and replay hash payload
HAS_LAYOUT → add normalized layout + layout_hash to receipt
```

Therefore merely upgrading the engine does not change the replay identity of historical no-layout matches.

`MatchResult.layout` is optional and appended to the dataclass contract so old manual constructions remain valid.

### Replay / WorldGraph / tournament propagation

Fixed layout identity participates in replay hashing and deterministic reruns. WorldGraph receives an `arena_layout` entity. `run_round_robin(..., layout=...)` propagates the same geometry to every seed/orientation.

### GameSpec integration

GameSpec 0.1 gains optional `layout`. Compiler checks:

```text
environment dimensions == layout dimensions
layout structural validity
connectivity/resource reachability
configured asymmetry threshold
resource_count := len(layout.resources)
```

The build receipt gains `layout_hash` and exact `LayoutAudit` only when a layout exists. No-layout compiled outputs retain their previous layout-free surface.

### Action vocabulary repair

Arena-T0 emits `stay`; R0.6 accepted `idle`. R0.7 canonicalizes this boundary:

```text
canonical action: stay
legacy input alias: idle → stay
```

Normalized specs and receipts therefore represent executable semantics rather than a phantom action name.

### Example

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
BUILD_RECEIPT != EXTERNAL_CERTIFICATION
OAK_ACCEPTED_BUILD != SCIENTIFIC_TRUTH
DETERMINISTIC_REPLAY != PHYSICAL_TRUTH
TOURNAMENT_WIN != GENERAL_INTELLIGENCE
QD_COVERAGE != BEHAVIORAL_COMPLETENESS
HALL_OF_FAME != GLOBAL_OPTIMALITY
M_PLUS != PROOF_OF_TRUTH
M_MINUS != PROOF_OF_IMPOSSIBILITY
HELD_OUT_SEEDS != REAL_WORLD_GENERALIZATION
ADVERSARIAL_SCORE != UNIVERSAL_DIFFICULTY
```

## R0.8+ roadmap

### R0.8 — adversarial layout evolution

- bounded mutation of resources/obstacles/spawns;
- connectivity-preserving repair or rejection;
- held-out map sets distinct from training maps;
- layout difficulty/discrimination receipts;
- map-generalization gaps;
- M- registry for invalid/unfair/dead layouts.

### R0.9 — scalable execution

- sharding;
- checkpoints;
- backpressure;
- profiler adapters;
- CPU/GPU scheduling experiments;
- empirical wall-clock/energy OAKBench.

No generated map, compiled game, evolved environment or benchmark champion is automatically considered fun, fair, safe, scientifically valid, generally intelligent or publishable.
