# Ω-GAME-SIM-EVO-T∞ / Ω-GENESIS-ENGINE-T∞

**Maturity:** R0.4 executable prototype  
**Host:** `omega_game_t`  
**Authority:** research / benchmark / review only

## Mother loop

```text
Generate → Simulate → Compete → Measure → Evolve → Generate+
                         ↓
               OAK / replay / M+ / M-
```

The implementation advances through small falsifiable units:

```text
R0.1 deterministic experiment
→ R0.2 sparse/event execution
→ R0.3 quality diversity
→ R0.4 evolutionary memory
→ R0.5 coevolution
→ R0.6 GameSpec compiler
```

Ω-GAME-SIM-EVO-T∞ extends the already-merged Ω-GAME-T `WorldGraph` / `OAKGate` lineage; it does not replace it.

## R0.1 — deterministic experimental substrate

R0.1 established Arena-T0, explicit seeds/configs/genomes, canonical replay hashes, mirrored tournaments, vector ratings, deterministic mutation/selection, WorldGraph projection, OAK audit and bounded fuzzing.

Practical reproduction tuple:

```text
(seed, ArenaConfig, left AgentGenome, right AgentGenome, code revision)
```

## R0.2 — sparse/event kernel

R0.2 operationalized:

```text
full scan:  C_t ~ |W_t|
sparse:     C_t ~ |ΔW_t|
```

using `DirtyFrontier`, `ScheduledEvent`, `SparseEventScheduler`, Temporal LOD, a deterministic dependency DAG, bounded batches and `CostGraph` work-unit accounting.

The benchmark boundary remains:

```text
WORK_UNIT_REDUCTION != WALL_CLOCK_SPEEDUP
WORK_UNIT_REDUCTION != ENERGY_REDUCTION
DEPENDENCY_DAG != THREAD_SAFETY
```

## R0.3 — quality diversity

R0.3 introduced deterministic MAP-Elites-style storage over bounded genome projections.

Default descriptor:

```text
(aggression, exploration)
```

For coordinate `x ∈ [0,1]` and `B` bins:

```text
cell(x) = min(B - 1, floor(B x))
```

Each archive cell retains the highest-quality elite, with deterministic `agent_id` tie-breaking. Novelty is normalized k-nearest Euclidean distance in the chosen descriptor projection.

Archive metrics include coverage, QD score, mean/max quality and mean novelty.

```text
QD_COVERAGE != BEHAVIORAL_COMPLETENESS
QD_SCORE != GENERAL_INTELLIGENCE
NOVELTY != USEFULNESS
NOVELTY != SCIENTIFIC_OR_PATENT_NOVELTY
```

## R0.4 — evolutionary memory / anti-forgetting

### Why memory is a first-class engine component

A purely generational optimizer can improve its current benchmark while silently losing historical capabilities. R0.4 therefore changes the evolution loop from:

```text
population_t → select → population_t+1
```

into:

```text
population_t
→ tournament / OAK
→ M+ champions
→ M- failures
→ Hall of Fame
→ next population
→ historical regression
```

The system now preserves both what worked and what failed.

### ChampionRecord / HallOfFame

A `ChampionRecord` stores:

```text
generation
rank
normalized AgentGenome
RatingVector
quality
tournament seeds
receipt_hash
```

The receipt hash is SHA-256 over the canonical tournament-derived champion payload. It provides deterministic identity/provenance, not external certification.

`HallOfFame.admit` takes a tournament and the exact population covered by its ratings, selects `top_k`, and stores immutable-by-receipt champion records.

The Hall of Fame is an archive of historically strong benchmark participants:

```text
HALL_OF_FAME != GLOBAL_OPTIMALITY
HALL_OF_FAME != GENERAL_INTELLIGENCE
```

### M+ / M-

`MemoryRecord` has explicit polarity:

```text
plus  = useful result retained as positive evidence
minus = failure/counterexample retained as negative evidence
```

Every record has a canonical evidence hash and deterministic ID.

`EvolutionaryMemory` maintains separate stores:

```text
hall_of_fame
m_plus
m_minus
```

Tournament champions automatically become `M+ / champion` records.

Fuzzer failures become `M- / fuzz_failure` records containing:

```text
campaign_seed
case_index
case_seed
failure flags
```

Repeated ingestion is deduplicated by deterministic memory ID.

The epistemic boundary is strict:

```text
M_PLUS != PROOF_OF_TRUTH
M_MINUS != PROOF_OF_IMPOSSIBILITY
```

M+ says "retain this successful evidence under the recorded conditions." M- says "do not forget this observed failure/counterexample under the recorded conditions."

### Anti-forgetting tournament

`evaluate_anti_forgetting` extracts historical challenge agents from the Hall of Fame and plays the candidate against each champion under explicit fixed seeds in both orientations.

For every historical champion `h`:

```text
candidate vs h
h vs candidate
```

are run for each challenge seed.

Scoring:

```text
win  = 1 point
draw = 0.5 point
loss = 0 points
```

Aggregate score:

```text
F = candidate_points / available_points
```

and project policy:

```text
passed = F >= threshold
```

The threshold is configurable and belongs to the benchmark contract. Therefore:

```text
ANTI_FORGETTING_THRESHOLD != UNIVERSAL_PROGRESS_CRITERION
PASS != PROOF_OF_MONOTONIC_INTELLIGENCE
FAIL != PROOF_THAT_NEW_AGENT_IS_GLOBALLY_WORSE
```

It measures only performance against the recorded historical challenge set.

### Memory as negative-computation reduction

M- also creates a computational optimization opportunity:

```text
failed state / mutation / seed
→ canonical memory hash
→ regression fixture or prefilter
→ avoid rediscovering identical failure blindly
```

Future work can generalize exact hashes into similarity neighborhoods, but R0.4 deliberately keeps exact deterministic provenance separate from heuristic generalization.

## CLI

From `omega_game_t/`:

```bash
PYTHONPATH=. python -m omega_game arena --seed 42 --steps 96
PYTHONPATH=. python -m omega_game tournament --seed 42 --population 8 --steps 64
PYTHONPATH=. python -m omega_game evolve --seed 42 --population 8 --generations 3 --steps 48
PYTHONPATH=. python -m omega_game quality-diversity --seed 42 --population 16 --steps 48 --bins 8
PYTHONPATH=. python -m omega_game memory-demo --seed 42 --population 8 --top-k 3 --steps 32 --threshold 0.5
PYTHONPATH=. python -m omega_game fuzz --seed 42 --cases 100
PYTHONPATH=. python -m omega_game sparse-bench --seed 42 --entities 10000 --active 100 --ticks 128
```

## OAK boundary ledger

```text
DETERMINISTIC_REPLAY != PHYSICAL_TRUTH
TOURNAMENT_WIN != GENERAL_INTELLIGENCE
SIMULATION_EVOLUTION != BIOLOGICAL_EVOLUTION
WORK_UNIT_REDUCTION != WALL_CLOCK_SPEEDUP
QD_COVERAGE != BEHAVIORAL_COMPLETENESS
NOVELTY != USEFULNESS
HALL_OF_FAME != GLOBAL_OPTIMALITY
M_PLUS != PROOF_OF_TRUTH
M_MINUS != PROOF_OF_IMPOSSIBILITY
ANTI_FORGETTING_THRESHOLD != UNIVERSAL_PROGRESS_CRITERION
```

## Executable operating laws

```text
reproducibility before scale
headless benchmark before rendering
mirrored competition before champion claims
vector rating before scalar prestige
active frontier before total-world scanning
cost accounting before speed claims
ecology of elites before single-champion collapse
positive memory plus negative memory
historical regression before declaring progress
counterexamples before canonization
```

## R0.5–R0.7 roadmap

### R0.5 — coevolution

- agents ↔ maps;
- map genome / terrain parameters;
- adversarial map search;
- hidden validation seeds;
- generalization gap reports.

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

### R0.7 — scalable execution experiments

- sharding;
- checkpoints;
- backpressure;
- hardware profiler adapters;
- CPU/GPU scheduling experiments;
- empirical wall-clock/energy OAKBench.

No generated game, evolved agent or benchmark champion is automatically considered fun, fair, safe, scientifically valid, generally intelligent or publishable.
