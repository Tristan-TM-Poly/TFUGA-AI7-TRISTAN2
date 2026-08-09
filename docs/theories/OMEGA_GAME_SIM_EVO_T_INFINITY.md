# Ω-GAME-SIM-EVO-T∞ / Ω-GENESIS-ENGINE-T∞

**Maturity:** R0.6 executable prototype  
**Host:** `omega_game_t`  
**Authority:** research / benchmark / review only

## Mother architecture

```text
GameSpec / generators
→ bounded compilation
→ WorldGraph + ArenaConfig + RuleKernel + agents
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
```

Ω-GAME-SIM-EVO-T∞ extends the already-merged Ω-GAME-T `WorldGraph` / `OAKGate` lineage; it does not replace it.

## R0.1–R0.5 retained

### R0.1 — deterministic substrate

Arena-T0 provides explicit seeds/configs/genomes, replay SHA-256 identity, mirrored tournaments, vector ratings, deterministic mutation/selection, WorldGraph projection, OAK audit and bounded fuzzing.

### R0.2 — sparse/event kernel

Dirty frontiers, scheduled events, Temporal LOD, dependency DAGs, bounded batches and deterministic work-unit accounting operationalize the design target `cost ~ active frontier`.

### R0.3 — quality diversity

A deterministic MAP-Elites-style archive preserves strong but behaviorally distinct agents instead of collapsing the search to one scalar champion.

### R0.4 — evolutionary memory

Tournament champions become Hall-of-Fame/M+ evidence; fuzz failures become M- evidence; candidates are regressed against distinct historical champions to expose forgetting.

### R0.5 — agent↔environment coevolution

Bounded environment genomes compile to ArenaConfig, environments are evaluated on disjoint train/validation seeds, and agents receive explicit generalization-gap/worst-case receipts. Environments can evolve under a documented adversarial benchmark score.

## R0.6 — GameSpec as bounded intermediate representation

### Why a compiler layer

Before R0.6, engine objects had to be constructed through Python APIs or specialized CLI commands. R0.6 introduces a declarative source representation:

```text
GameSpec
→ validation
→ normalized IR
→ existing engine primitives
```

The design goal is not unrestricted game-program synthesis. It is a small deterministic compiler whose accepted language is reviewable and testable.

### GameSpec 0.1

Top-level fields are limited to:

```text
spec_id
version
environment
agents
rules
metadata
```

Unknown fields fail closed at the top level and in environment/agent/rule records.

Current version:

```text
GAME_SPEC_VERSION = "0.1"
```

Unsupported versions fail rather than being guessed or migrated silently.

### Agent IR

`GameAgentSpec` supports only:

```text
agent_id
seek_resource
aggression
conservation
exploration
```

It lowers through the already-tested `AgentGenome.normalized()` contract. Agent IDs must be unique and a compiled GameSpec requires at least two agents.

### Environment IR

`GameEnvironmentSpec` supports the current Arena-T0 parameter family:

```text
width, height
resource_density
initial_energy
harvest_energy
move_cost
attack_cost
attack_damage
max_steps
```

Lowering path:

```text
GameEnvironmentSpec
→ EnvironmentGenome(normalized)
→ ArenaConfig
→ ArenaConfig.validate()
```

Therefore the compiler reuses R0.5's environment bounds instead of defining a second inconsistent environment model.

### Rule IR

R0.6 deliberately uses a tiny action vocabulary:

```text
attack
harvest
idle
move
```

Unknown actions fail closed. `GameRuleSpec` lowers to the historical `RuleKernel` with required actor kind `arena_agent`.

```text
RULE_VOCABULARY != COMPLETE_GAME_LOGIC
```

The rule surface is a bounded contract for the current Arena-T0 adapter, not a universal game DSL.

### WorldGraph lowering

Each compiled normalized agent becomes a `WorldGraph` entity of kind `arena_agent`.

```text
GameSpec agents
→ AgentGenome[]
→ Entity[]
→ WorldGraph("gamespec:<id>:<version>")
```

The world graph is then available to the existing game-quality/OAK machinery.

### OAK compilation gate

The compiler evaluates a bounded payload containing:

```text
normalized GameSpec
WorldGraph
ArenaConfig
```

through `OAKGate`.

A compiled artifact can exist with `accepted = false`, but `CompiledGame.run_tournament()` refuses execution in that state.

```text
parse success
!= compile acceptance
!= tournament authorization
```

This distinction is essential for future generated specifications.

### Deterministic build receipt

Every compiled build receives SHA-256 identity over canonical JSON containing:

```text
compiler identity
GameSpec version
normalized spec
ArenaConfig
RuleKernel contract
WorldGraph ID
OAK report
```

Thus equivalent normalized agent ordering produces the same receipt.

```text
BUILD_RECEIPT = deterministic provenance identity
BUILD_RECEIPT != external certification
```

### No arbitrary code execution

The compiler never accepts:

- Python source;
- import/module names;
- shell commands;
- callback names;
- dynamic expression strings;
- executable hooks.

The schema and parser use an allow-list model. A field such as `execute_python` or an action such as `shell_exec` fails as unknown/unsupported.

### JSON Schema

A machine-readable structural schema is stored at:

```text
omega_game_t/schemas/game_spec.schema.json
```

The runtime parser remains authoritative for R0.6 because it performs normalization and semantic checks beyond raw JSON shape.

Example:

```text
omega_game_t/examples/game_spec_arena_t0.json
```

### Compiler-to-tournament path

For an OAK-accepted build:

```text
GameSpec
→ GameSpecCompiler.compile
→ CompiledGame
→ run_tournament(seeds, mirrored=True)
→ TournamentReport
```

The CLI exposes the same path:

```bash
PYTHONPATH=. python -m omega_game compile-spec examples/game_spec_arena_t0.json --seed 42 --tournament
```

## OAK boundary ledger

```text
COMPILED_SPEC != FUN_GAME
COMPILED_SPEC != FAIR_GAME
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
specification before code generation
allow-list before extensibility
normalization before hashing
OAK before execution
reproducibility before scale
headless benchmark before rendering
mirrored competition before champion claims
active frontier before total-world scanning
ecology of elites before single-champion collapse
historical regression before declaring progress
held-out seeds before generalization claims
counterexamples before canonization
```

## R0.7+ roadmap

### R0.7 — explicit fixed map layouts

Extend GameSpec with bounded map geometry rather than only environment parameters:

```text
layout
→ bounds/connectivity validation
→ spawn/resource invariants
→ layout hash
→ train/validation map split
→ adversarial layout search
```

### R0.8 — scalable execution experiments

- sharding;
- checkpoints;
- backpressure;
- hardware profiler adapters;
- CPU/GPU scheduling experiments;
- empirical wall-clock/energy OAKBench.

### R0.9 — richer adapters

- TextWorld;
- Quest-CVCD;
- additional simulation domains;
- each behind explicit typed adapter contracts.

No compiled/generated game, evolved environment or benchmark champion is automatically considered fun, fair, safe, scientifically valid, generally intelligent or publishable.
