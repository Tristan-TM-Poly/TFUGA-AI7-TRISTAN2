# Ω-GAME-SIM-EVO-T∞ / Ω-GENESIS-ENGINE-T∞

**Maturity:** R0.3 executable prototype  
**Host:** `omega_game_t`  
**Authority:** research / benchmark / review only

## Mother loop

```text
Generate → Simulate → Compete → Measure → Evolve → Generate+
                         ↓
                 OAK / M- / replay
```

The objective is not to claim a universal game engine. The branch is built as a sequence of small falsifiable units:

```text
R0.1 deterministic experiment
→ R0.2 sparse/event execution
→ R0.3 quality diversity
→ R0.4 evolutionary memory
→ R0.5 coevolution
→ R0.6 GameSpec compiler
```

## Existing lineage reused

Ω-GAME-SIM-EVO-T∞ extends the already-merged Ω-GAME-T core rather than replacing it:

- `WorldGraph`, `Entity`, `Event`, `RuleKernel` remain structural primitives;
- `OAKGate` remains the review/safety gate;
- `omega_game_t_ci.yml` remains the CI authority;
- LanguageGM engines remain untouched;
- each new research layer is introduced through a separate tested split.

## R0.1 — deterministic experimental substrate

R0.1 introduced:

- `ArenaConfig`, `AgentGenome`, `AgentState`, `MatchResult`, `run_arena_t0`;
- deterministic RNG from explicit seeds;
- canonical replay SHA-256 receipts;
- mirrored multi-seed round-robin tournaments;
- vector `RatingVector` metrics;
- deterministic evolutionary selection/mutation;
- replay → `WorldGraph` projection;
- OAK/determinism audits;
- bounded fuzzing.

A practical reproduction tuple is:

```text
(seed, ArenaConfig, left AgentGenome, right AgentGenome, code revision)
```

Core boundaries:

```text
DETERMINISTIC_REPLAY != PHYSICAL_TRUTH
TOURNAMENT_WIN != GENERAL_INTELLIGENCE
SIMULATION_EVOLUTION != BIOLOGICAL_EVOLUTION
```

## R0.2 — Sparse/Event Kernel

R0.2 operationalized the target law:

```text
full scan:  C_t ~ |W_t|
sparse:     C_t ~ |ΔW_t|
```

through:

- `DirtyFrontier`;
- `ScheduledEvent`;
- `SparseEventScheduler`;
- `TemporalSignal` and `TemporalLODPolicy`;
- deterministic dependency DAG;
- bounded `max_batch` dispatch;
- `CostGraph` work accounting;
- `run_sparse_benchmark`.

Temporal signal:

```text
σ = (activity, importance, uncertainty, visible)
```

Default bounded score:

```text
s = 0.45 activity + 0.35 importance + 0.20 uncertainty
```

with visibility as a realtime override. Default cadences are 1/2/8/32 ticks for realtime/active/background/dormant systems. These values are configuration choices, not physical constants.

The sparse benchmark reports deterministic work units:

```text
W_naive  = total_entities × ticks
W_sparse = processed_active_entities
R        = 1 - W_sparse / W_naive
```

It does not establish equivalent wall-clock or energy reduction.

```text
WORK_UNIT_REDUCTION != WALL_CLOCK_SPEEDUP
WORK_UNIT_REDUCTION != ENERGY_REDUCTION
DEPENDENCY_DAG != THREAD_SAFETY
```

## R0.3 — Quality Diversity / MAP-Elites

### Motivation

A single champion collapses a multidimensional search into one winner. Ω-GAME-SIM-EVO-T∞ instead needs an ecology of strong but behaviorally distinct solutions.

R0.3 therefore introduces the objective:

```text
maximize quality
while preserving coverage of behavior space
```

rather than only:

```text
argmax_agent scalar_fitness(agent)
```

### BehaviorDescriptor

The current genome is bounded in four coordinates:

```text
seek_resource
aggression
conservation
exploration
```

`ArchiveConfig.axes` selects any subset of these coordinates as the current behavior projection. The default is:

```text
(aggression, exploration)
```

For axis value `x ∈ [0,1]` and `B` bins:

```text
cell(x) = min(B - 1, floor(B x))
```

The multidimensional archive cell is the Cartesian tuple of these indices.

The descriptor is a **chosen projection of behavior**, not a complete behavioral ontology.

### MapElitesArchive

Each cell stores at most one `EliteRecord`:

```text
cell
agent
behavior descriptor
quality
rating evidence
```

Insertion law:

```text
empty cell → accept candidate
higher quality → replace elite
equal quality → deterministic agent_id tie-break
lower quality → reject candidate
```

This produces a deterministic MAP-Elites-style archive for a fixed population and tournament receipt.

### Cell quality

R0.3 uses `quality_from_rating` only for **within-cell elite selection**:

```text
Q = points
  + 0.01 score_delta
  + 0.50 robustness
  + 0.05 efficiency
  + 0.25 stability
```

The coefficients are benchmark configuration choices. They are not universal measures of intelligence or game quality.

### Archive novelty

For descriptor `d`, novelty is the mean normalized Euclidean distance to up to `k` nearest occupied elite descriptors:

```text
N(d) = mean_k( ||d - d_i||_2 / sqrt(dim) )
```

Hence for bounded coordinates:

```text
0 <= N <= 1
```

Novelty is descriptive distance in the chosen projection. It is not usefulness, creativity, scientific novelty, or patent novelty.

### QualityDiversityReport

The report exposes:

```text
occupied_cells
total_cells
coverage
qd_score
mean_quality
max_quality
mean_novelty
elite records
```

with:

```text
coverage = occupied_cells / total_cells
qd_score = Σ max(0, elite_quality)
```

These are archive metrics. In particular:

```text
HIGH_COVERAGE != COMPLETE_BEHAVIOR_SPACE
HIGH_QD_SCORE != GENERAL_INTELLIGENCE
HIGH_NOVELTY != USEFUL_INNOVATION
```

### Tournament → archive pipeline

`run_quality_diversity` composes the existing R0.1 tournament with R0.3:

```text
population
→ mirrored multi-seed tournament
→ RatingVector per agent
→ behavior projection
→ archive cell
→ elite competition
→ quality-diversity report
```

This preserves a single evidence path rather than inventing a second evaluation engine.

## CLI

From `omega_game_t/`:

```bash
PYTHONPATH=. python -m omega_game arena --seed 42 --steps 96
PYTHONPATH=. python -m omega_game tournament --seed 42 --population 8 --steps 64
PYTHONPATH=. python -m omega_game evolve --seed 42 --population 8 --generations 3 --steps 48
PYTHONPATH=. python -m omega_game quality-diversity --seed 42 --population 16 --steps 48 --bins 8
PYTHONPATH=. python -m omega_game fuzz --seed 42 --cases 100
PYTHONPATH=. python -m omega_game sparse-bench --seed 42 --entities 10000 --active 100 --ticks 128
```

## OAK boundaries

```text
DETERMINISTIC_REPLAY != PHYSICAL_TRUTH
TOURNAMENT_WIN != GENERAL_INTELLIGENCE
SIMULATION_EVOLUTION != BIOLOGICAL_EVOLUTION
WORK_UNIT_REDUCTION != WALL_CLOCK_SPEEDUP
WORK_UNIT_REDUCTION != ENERGY_REDUCTION
DEPENDENCY_DAG != THREAD_SAFETY
QD_COVERAGE != BEHAVIORAL_COMPLETENESS
QD_SCORE != GENERAL_INTELLIGENCE
NOVELTY != USEFULNESS
NOVELTY != SCIENTIFIC_OR_PATENT_NOVELTY
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
ecology of elites before single-champion collapse
explicit descriptor projection before claims of diversity
```

## R0.4–R0.6 roadmap

### R0.4 — evolutionary memory

- Hall of Fame;
- extinct-lineage registry;
- explicit M+ / M- stores;
- regression challenge set from historical failures/champions;
- anti-forgetting tournament fixtures.

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
