# Ω-GAME-SIM-EVO-T∞ / Ω-GENESIS-ENGINE-T∞

**Maturity:** R0.5 executable prototype  
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
→ R0.5 agent↔environment coevolution
→ R0.6 GameSpec compiler
```

Ω-GAME-SIM-EVO-T∞ extends the already-merged Ω-GAME-T `WorldGraph` / `OAKGate` lineage; it does not replace it.

## R0.1 — deterministic experimental substrate

Arena-T0 establishes explicit seeds/configs/genomes, canonical replay hashes, mirrored tournaments, vector ratings, deterministic mutation/selection, WorldGraph projection, OAK audit and bounded fuzzing.

```text
DETERMINISTIC_REPLAY != PHYSICAL_TRUTH
TOURNAMENT_WIN != GENERAL_INTELLIGENCE
SIMULATION_EVOLUTION != BIOLOGICAL_EVOLUTION
```

## R0.2 — sparse/event kernel

R0.2 operationalizes the target law:

```text
full scan:  C_t ~ |W_t|
sparse:     C_t ~ |ΔW_t|
```

through `DirtyFrontier`, scheduled events, Temporal LOD, a dependency DAG, bounded batches and deterministic `CostGraph` work-unit accounting.

```text
WORK_UNIT_REDUCTION != WALL_CLOCK_SPEEDUP
WORK_UNIT_REDUCTION != ENERGY_REDUCTION
DEPENDENCY_DAG != THREAD_SAFETY
```

## R0.3 — quality diversity

R0.3 introduces deterministic MAP-Elites-style storage over chosen bounded genome projections. Each behavior cell retains one elite; the archive reports coverage, QD score, quality and normalized descriptor-space novelty.

```text
QD_COVERAGE != BEHAVIORAL_COMPLETENESS
QD_SCORE != GENERAL_INTELLIGENCE
NOVELTY != USEFULNESS
NOVELTY != SCIENTIFIC_OR_PATENT_NOVELTY
```

## R0.4 — evolutionary memory / anti-forgetting

R0.4 makes historical evidence first-class:

```text
population
→ tournament/OAK
→ Hall of Fame + M+
→ fuzz/counterexamples + M-
→ next generation
→ historical regression
```

Champion records carry deterministic tournament-derived receipts. M+ stores useful positive benchmark evidence; M- stores observed failures/counterexamples. Anti-forgetting tests new candidates against distinct historical champions on explicit mirrored seeds.

```text
HALL_OF_FAME != GLOBAL_OPTIMALITY
M_PLUS != PROOF_OF_TRUTH
M_MINUS != PROOF_OF_IMPOSSIBILITY
ANTI_FORGETTING_THRESHOLD != UNIVERSAL_PROGRESS_CRITERION
```

## R0.5 — agent ↔ environment coevolution

### Goal

A fixed environment encourages agents to specialize to one narrow benchmark. R0.5 makes the environment itself an explicit bounded genome and separates environment **training seeds** from **held-out validation seeds**.

The new loop is:

```text
agent population A_t
×
environment population E_t
→ train tournaments
→ held-out validation tournaments
→ agent generalization receipts
→ environment difficulty/discrimination receipts
→ adversarial environment selection
→ mutate E_t
→ E_t+1
```

R0.5 deliberately evolves parameterized Arena-T0 environments rather than claiming to generate arbitrary game levels.

### EnvironmentGenome

`EnvironmentGenome` contains bounded Arena-T0 parameters:

```text
environment_id
width, height
resource_density
initial_energy
harvest_energy
move_cost
attack_cost
attack_damage
max_steps
```

Normalization clamps every dimension into a finite documented domain. `to_config()` compiles the normalized genome into a validated `ArenaConfig`; resource density is converted to a bounded integer resource count.

This creates the compiler boundary:

```text
EnvironmentGenome
→ normalization
→ ArenaConfig
→ ArenaConfig.validate()
→ tournament
```

An environment genome is a parameter vector, not a complete map layout or semantic game description.

### Deterministic environment generation

`seed_environments(count, seed)` creates a finite reproducible environment population. Each environment has a stable unique ID and parameters derived only from the explicit seed and generation procedure.

### Train / validation separation

`run_coevolution_cycle` requires:

```text
train_seeds ∩ validation_seeds = ∅
```

Overlap fails closed. Each environment is evaluated twice using exactly the same agent population:

```text
T_train(e) = round_robin(A, train_seeds, config=e)
T_val(e)   = round_robin(A, validation_seeds, config=e)
```

Held-out seeds reduce one obvious form of seed overfitting; they do not establish real-world or out-of-distribution generalization.

### Environment difficulty

For each tournament, R0.5 computes mean agent efficiency and the bounded benchmark difficulty:

```text
D = 1 / (1 + max(0, mean_efficiency))
```

so lower measured efficiency corresponds to a larger `D` within this benchmark.

Validation discrimination is the population standard deviation of tournament-derived agent quality under that environment:

```text
S = std_pop(Q_agent)
```

Current adversarial score:

```text
A_env = D_validation + 0.10 S_validation
```

The coefficient `0.10` is a benchmark policy. It can be changed or replaced later through OAKBench comparisons.

```text
ADVERSARIAL_SCORE != UNIVERSAL_DIFFICULTY
LOW_EFFICIENCY != BAD_GAME
HIGH_DISCRIMINATION != FAIRNESS
```

### Agent generalization receipt

For every agent across the environment population, R0.5 records:

```text
train_mean_quality
validation_mean_quality
generalization_gap = train_mean - validation_mean
worst_validation_quality
validation_quality_std
```

This distinguishes average performance from worst-environment behavior and validation variability.

```text
HELD_OUT_SEEDS != REAL_WORLD_GENERALIZATION
SMALL_GENERALIZATION_GAP != GENERAL_INTELLIGENCE
```

### Environment receipts

Each `EnvironmentEvaluation` carries a SHA-256 receipt over:

```text
environment genome
train seeds
validation seeds
train/validation efficiency
train/validation difficulty
validation discrimination
```

The whole `CoevolutionReport` also receives a deterministic canonical receipt hash. These hashes provide reproducible identity/provenance, not external certification.

### Adversarial environment evolution

`evolve_environments` ranks environments by the recorded adversarial score, preserves a bounded elite fraction, then creates a target-size next population through deterministic bounded mutation.

Mutated fields include dimensions, resource density, energy/cost parameters, damage and maximum steps. Every child is normalized before use.

```text
E_t
→ validation adversarial ranking
→ elites
→ deterministic mutation(seed, generation)
→ normalize
→ E_t+1
```

This is computational coevolution inside Arena-T0. It is not biological evolution and does not imply that a harder benchmark is a better game.

## CLI

From `omega_game_t/`:

```bash
PYTHONPATH=. python -m omega_game arena --seed 42 --steps 96
PYTHONPATH=. python -m omega_game tournament --seed 42 --population 8 --steps 64
PYTHONPATH=. python -m omega_game evolve --seed 42 --population 8 --generations 3 --steps 48
PYTHONPATH=. python -m omega_game quality-diversity --seed 42 --population 16 --steps 48 --bins 8
PYTHONPATH=. python -m omega_game memory-demo --seed 42 --population 8 --top-k 3 --steps 32 --threshold 0.5
PYTHONPATH=. python -m omega_game coevolve --seed 42 --population 6 --environments 4 --adversarial-limit 2 --next-environments 4
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
HELD_OUT_SEEDS != REAL_WORLD_GENERALIZATION
ADVERSARIAL_SCORE != UNIVERSAL_DIFFICULTY
ENVIRONMENT_GENOME != COMPLETE_LEVEL_DESCRIPTION
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
held-out seeds before generalization claims
coevolve challenges without confusing hardness with quality
counterexamples before canonization
```

## R0.6–R0.8 roadmap

### R0.6 — GameSpec compiler

```text
GameSpec
→ bounded schema validation
→ WorldGraph/ECS-style projection
→ Arena adapter
→ agent API
→ tournament adapter
→ OAK tests
→ deterministic build receipt
```

### R0.7 — explicit map layouts / adversarial level generation

- fixed resource/obstacle layouts;
- map hashes;
- connectivity/fairness gates;
- train/validation map splits;
- adversarial map search distinct from environment-parameter search.

### R0.8 — scalable execution experiments

- sharding;
- checkpoints;
- backpressure;
- hardware profiler adapters;
- CPU/GPU scheduling experiments;
- empirical wall-clock/energy OAKBench.

No generated environment, evolved agent or benchmark champion is automatically considered fun, fair, safe, scientifically valid, generally intelligent or publishable.
