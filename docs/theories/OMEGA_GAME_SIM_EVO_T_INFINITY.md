# Ω-GAME-SIM-EVO-T∞ / Ω-GENESIS-ENGINE-T∞

**Maturity:** R0.2 executable prototype  
**Host:** `omega_game_t`  
**Authority:** research / benchmark / review only

## Mother loop

```text
Generate → Simulate → Compete → Measure → Evolve → Generate+
                         ↓
                 OAK / M- / replay
```

The objective is not to claim a universal game engine. R0.1 established a falsifiable substrate where deterministic simulation, tournaments, evolution and OAK verification share one data path. R0.2 adds a sparse/event-driven execution layer so computational attention can follow the active causal frontier rather than the entire represented world.

## Existing lineage reused

Ω-GAME-SIM-EVO-T∞ extends the already-merged Ω-GAME-T core rather than replacing it:

- `WorldGraph`, `Entity`, `Event`, `RuleKernel` remain structural primitives;
- `OAKGate` remains the review/safety gate;
- `omega_game_t_ci.yml` remains the CI authority;
- existing LanguageGM engines remain untouched;
- R0.1 Arena/Tournament/Evolution APIs remain compatible.

The previous large Ω-GAME-T PR was intentionally split; this implementation continues the smaller-unit strategy.

## R0.1 — deterministic experimental substrate

### Arena-T0

`ArenaConfig`, `AgentGenome`, `AgentState`, `MatchResult`, `run_arena_t0`

Arena-T0 is a deterministic headless grid benchmark with resource collection, movement/energy cost, adjacent combat, alternating first-move order, bounded genome parameters, explicit seeds and canonical replay hashing.

A practical reproduction tuple is:

```text
(seed, ArenaConfig, left AgentGenome, right AgentGenome, code revision)
```

### Tournament-T0

`RatingVector`, `TournamentReport`, `run_round_robin`

R0.1 supports mirrored multi-seed round robin and vector ratings:

```text
wins, draws, losses,
score_for, score_against,
robustness, efficiency, novelty, stability
```

Mirroring reduces orientation bias; it does not prove a game or benchmark is globally fair.

### Evolution-T0

`EvolutionConfig`, `GenerationReport`, `EvolutionRun`, `seed_population`, `evolve_generation`, `evolve`

The genome spans bounded `seek_resource`, `aggression`, `conservation`, and `exploration`. Selection combines tournament performance with bounded novelty/robustness/efficiency terms. Elites are retained and children receive deterministic Gaussian mutations from generation-specific seeds.

This is algorithmic evolution. It is not a biological model.

### WorldGraph + OAK bridge

`match_world_graph` projects replay events into the historical Ω-GAME-T graph core:

```text
Arena-T0 replay → Entity/Event graph → GameQualityScore → OAKGate
```

`audit_match` checks config validity, tick bounds, winner identity, non-negative terminal quantities, replay SHA-256 integrity, exact deterministic rerun, WorldGraph quality and OAK acceptance.

`fuzz_arena_t0` samples bounded arenas/genomes/seeds and records invariant failures for future M- regression memory.

## R0.2 — Sparse/Event Kernel

### Sparse-world law

The target optimization law is:

```text
full scan:  C_t ~ |W_t|
sparse:     C_t ~ |ΔW_t|
```

where `|ΔW_t|` is represented operationally by dirty entities and due causal events. This is an algorithmic design objective, not a universal asymptotic theorem for every game workload.

### DirtyFrontier

`DirtyFrontier` is a deterministic deduplicated frontier of entity IDs requiring recomputation. It supports bounded consumption through `max_batch` so a system cannot consume an unbounded dirty set in one dispatch.

### EventScheduler

`ScheduledEvent` carries:

```text
(tick, event_id, system_id, entity_id?, payload)
```

`SparseEventScheduler` stores future events in deterministic `(tick, insertion-sequence)` order. When an event becomes due it can wake a dormant system immediately and, when an entity ID is supplied, place that entity on the dirty frontier.

### Temporal LOD

A temporal signal is:

```text
σ = (activity, importance, uncertainty, visible)
```

R0.2 uses the bounded score:

```text
s = 0.45 activity + 0.35 importance + 0.20 uncertainty
```

with visibility as an explicit realtime override. `TemporalLODPolicy` maps the signal to one of four cadences:

```text
realtime → every 1 tick
active → every 2 ticks
background → every 8 ticks
dormant → every 32 ticks
```

These defaults are configuration choices, not physical constants.

A system may opt into immediate dirty/event wakeups or choose to preserve its coarser cadence. This separates **causal wakeup** from **periodic fidelity**.

### Dependency DAG

Each `SystemSpec` can declare dependencies. The scheduler performs a deterministic topological ordering:

```text
dependency constraints
→ ready set
→ priority order inside ready set
→ stable system_id tie-break
```

Unknown dependencies and cycles fail closed. The DAG controls dispatch ordering; it does not by itself prove semantic independence, thread safety, or safe parallel execution.

### CostGraph

`CostGraph` records deterministic work accounting per system:

```text
invocations
processed_entities
processed_events
estimated_work
```

with:

```text
estimated_work = n_entities * cost_per_entity
               + n_events * cost_per_event
```

This is intentionally not a wall-clock profiler.

### Sparse benchmark

`run_sparse_benchmark` compares a full-scan baseline against the sparse active frontier under a common one-work-unit-per-entity accounting assumption:

```text
W_naive  = total_entities × ticks
W_sparse = processed_active_entities
R        = 1 - W_sparse / W_naive
```

For example, 1000 represented entities with 25 active entities across 20 ticks produce:

```text
W_naive  = 20,000
W_sparse = 500
R        = 0.975
```

This proves only the accounting identity for that workload. It does **not** establish a 97.5% wall-clock speedup. Scheduler overhead, cache behavior, branch prediction, allocator behavior, GPU occupancy, synchronization and hardware energy remain empirical questions for later OAKBench layers.

## CLI

From `omega_game_t/`:

```bash
PYTHONPATH=. python -m omega_game arena --seed 42 --steps 96
PYTHONPATH=. python -m omega_game tournament --seed 42 --population 8 --steps 64
PYTHONPATH=. python -m omega_game evolve --seed 42 --population 8 --generations 3 --steps 48
PYTHONPATH=. python -m omega_game fuzz --seed 42 --cases 100
PYTHONPATH=. python -m omega_game sparse-bench --seed 42 --entities 10000 --active 100 --ticks 128
```

## OAK boundaries

```text
DETERMINISTIC_REPLAY != PHYSICAL_TRUTH
TOURNAMENT_WIN != GENERAL_INTELLIGENCE
NOVELTY_SCORE != USEFUL_INNOVATION
SIMULATION_EVOLUTION != BIOLOGICAL_EVOLUTION
WORK_UNIT_REDUCTION != WALL_CLOCK_SPEEDUP
WORK_UNIT_REDUCTION != ENERGY_REDUCTION
DEPENDENCY_DAG != THREAD_SAFETY
```

## Optimization laws now executable

```text
reproducibility before scale
headless benchmark before rendering
mirrored competition before champion claims
vector rating before scalar prestige
counterexamples before canonization
active frontier before total-world scanning
events before pointless polling
adaptive cadence before uniform frequency
cost accounting before speed claims
```

## R0.3–R0.6 roadmap

### R0.3 — quality diversity

- MAP-Elites archive;
- behavioral descriptors from genomes/replays;
- novelty archive;
- Pareto-like quality/diversity views.

### R0.4 — evolutionary memory

- Hall of Fame;
- extinct-lineage registry;
- explicit M+ / M- stores;
- regression challenge set from historical failures/champions.

### R0.5 — coevolution

- agents ↔ maps;
- agents ↔ adversaries;
- adversarial level generation;
- hidden validation seeds;
- anti-overfitting challenge sets.

### R0.6 — GameSpec compiler

```text
GameSpec
→ schema validation
→ ECS/HGFM projection
→ simulation adapter
→ agent API
→ tournament adapter
→ OAK tests
→ benchmark receipt
```

No generated game is automatically considered fun, fair, safe, scientifically valid or publishable.

## Long horizon

The Ω-GENESIS-ENGINE-T∞ target is a common experimental substrate for games, scientific simulations, artificial ecologies and algorithmic worlds. Each domain must preserve its own evidence boundary. A reproducible computational world can be an excellent experiment without being evidence that the same law holds in the physical world.
