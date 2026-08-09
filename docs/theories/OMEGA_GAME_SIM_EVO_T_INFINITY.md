# Ω-GAME-SIM-EVO-T∞ / Ω-GENESIS-ENGINE-T∞

**Maturity:** R0.1 executable prototype  
**Host:** `omega_game_t`  
**Authority:** research / benchmark / review only

## Mother loop

```text
Generate → Simulate → Compete → Measure → Evolve → Generate+
                         ↓
                 OAK / M- / replay
```

The objective is not to claim a universal game engine. R0.1 establishes a small falsifiable substrate where deterministic simulation, tournaments, evolution and OAK verification share one data path.

## Existing lineage reused

Ω-GAME-SIM-EVO-T∞ extends the already-merged Ω-GAME-T core rather than replacing it:

- `WorldGraph`, `Entity`, `Event`, `RuleKernel` remain the structural primitives;
- `OAKGate` remains the review/safety gate;
- `omega_game_t_ci.yml` remains the CI authority;
- existing LanguageGM engines remain untouched.

The previous large Ω-GAME-T PR was intentionally split; this implementation continues the smaller-unit strategy.

## R0.1 implemented objects

### Arena-T0

`ArenaConfig`, `AgentGenome`, `AgentState`, `MatchResult`, `run_arena_t0`

Arena-T0 is a deterministic headless grid benchmark with:

- resource collection;
- movement and energy cost;
- adjacent combat;
- alternating first-move order;
- bounded genome parameters;
- deterministic RNG from an explicit seed;
- canonical replay hashing.

A result is identified by the practical reproduction tuple:

```text
(seed, ArenaConfig, left AgentGenome, right AgentGenome, code revision)
```

### Tournament-T0

`RatingVector`, `TournamentReport`, `run_round_robin`

R0.1 supports mirrored multi-seed round robin. Ratings are vectorial rather than Elo-only:

```text
wins, draws, losses,
score_for, score_against,
robustness, efficiency, novelty, stability
```

Mirroring reduces orientation bias; it does not prove a game or benchmark is globally fair.

### Evolution-T0

`EvolutionConfig`, `GenerationReport`, `EvolutionRun`, `seed_population`, `evolve_generation`, `evolve`

The genome currently spans four bounded behavioral parameters:

```text
seek_resource, aggression, conservation, exploration
```

Selection uses tournament performance plus bounded novelty/robustness/efficiency terms. Elites are retained and children receive deterministic Gaussian mutations from a generation-specific seed.

This is algorithmic evolution. It is not a biological model.

### WorldGraph bridge

`match_world_graph` projects every replay into the historical Ω-GAME-T graph core:

```text
Arena-T0 replay → Entity/Event graph → GameQualityScore → OAKGate
```

This keeps the simulation lineage connected to the existing HGFM-oriented representation instead of creating a parallel silo.

### OAK / determinism

`audit_match` verifies:

- ArenaConfig validity;
- tick bounds;
- winner identity;
- non-negative energy and score;
- replay SHA-256 integrity;
- exact deterministic rerun under the same inputs;
- WorldGraph quality and OAK acceptance.

Core boundary:

```text
DETERMINISTIC_REPLAY != PHYSICAL_TRUTH
TOURNAMENT_WIN != GENERAL_INTELLIGENCE
NOVELTY_SCORE != USEFUL_INNOVATION
SIMULATION_EVOLUTION != BIOLOGICAL_EVOLUTION
```

### Game fuzzer

`fuzz_arena_t0` samples bounded random arenas, genomes and seeds, reruns them deterministically, and records invariant failures.

The fuzzer is designed to feed future M- memory:

```text
case → failure flags → minimal counterexample → regression test → M-
```

## CLI

From `omega_game_t/`:

```bash
PYTHONPATH=. python -m omega_game arena --seed 42 --steps 96
PYTHONPATH=. python -m omega_game tournament --seed 42 --population 8 --steps 64
PYTHONPATH=. python -m omega_game evolve --seed 42 --population 8 --generations 3 --steps 48
PYTHONPATH=. python -m omega_game fuzz --seed 42 --cases 100
```

## Current optimization laws

R0.1 encodes the architectural direction without pretending all optimization layers are implemented:

```text
cost ~ active state, not total imagined world size
reproducibility before scale
headless benchmark before rendering
mirrored competition before champion claims
vector rating before scalar prestige
counterexamples before canonization
```

## R0.2–R0.5 roadmap

### R0.2 — sparse/event kernel

- dirty-entity frontier;
- event queue;
- system dependency DAG;
- temporal LOD;
- sparse wake/sleep scheduling;
- scheduler telemetry.

### R0.3 — quality diversity

- MAP-Elites archive;
- behavioral descriptors from replays;
- novelty archive;
- Hall of Fame and extinct-lineage registry;
- explicit M+ / M- stores.

### R0.4 — coevolution

- agents ↔ maps;
- agents ↔ adversaries;
- adversarial level generation;
- hidden validation seeds;
- anti-overfitting challenge sets.

### R0.5 — GameSpec compiler

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

The long-term Ω-GENESIS-ENGINE-T∞ target is a common experimental substrate for games, scientific simulations, artificial ecologies and algorithmic worlds. Each domain must preserve its own evidence boundary. A reproducible computational world can be an excellent experiment without being evidence that the same law holds in the physical world.
