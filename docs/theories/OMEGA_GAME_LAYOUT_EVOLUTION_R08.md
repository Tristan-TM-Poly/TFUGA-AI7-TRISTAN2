# Ω-GAME-SIM-EVO-T∞ R0.8 — Adversarial Fixed-Layout Evolution

**Status:** executable candidate stacked on R0.7-v2  
**Authority:** benchmark/research only

## Core loop

```text
valid fixed layouts L_t
× agent population A
→ train-seed tournaments
→ held-out-seed tournaments
→ difficulty / discrimination / asymmetry receipts
→ adversarial ranking
→ elites
→ bounded layout mutations
→ connectivity/fairness rejection or admission
→ L_t+1
→ held-out map-set generalization
→ M+ / M-
```

R0.8 evolves explicit geometry rather than only R0.5 environment parameters.

## Mutation grammar

Current bounded mutations are intentionally small:

```text
move_resource
 toggle_obstacle = add_obstacle | remove_obstacle
```

Spawns and dimensions remain fixed in this first layout-evolution unit. Each candidate is checked by the R0.7 `ArenaLayout` structural/audit contract.

A mutation is admitted only if:

```text
candidate_hash != parent_hash
and ArenaLayout.audit(fairness_threshold).accepted
```

A bounded `repair_attempts` budget performs deterministic resampling/rejection. Failure to produce a valid child does not silently fall back to an invalid layout.

## Negative memory

Each rejected mutation can be recorded in `EvolutionaryMemory.M-` with:

```text
generation
parent_hash
seed
attempt
candidate_hash
operations
flags
```

Admitted mutations can be recorded in M+ as provenance of successful bounded transitions. M+ means admission under the current benchmark contract, not proof of map quality.

## Layout population evaluation

For each valid layout:

```text
T_train(layout) = mirrored tournament on train_seeds
T_val(layout)   = mirrored tournament on validation_seeds
```

Seeds must be disjoint.

Mean efficiency gives the bounded difficulty proxy:

```text
D = 1 / (1 + max(0, mean_efficiency))
```

Validation discrimination is the population standard deviation of tournament-derived agent quality.

Current adversarial ranking score:

```text
S_layout =
    w_D * D_validation
  + w_disc * discrimination_validation
  - w_asym * resource_distance_asymmetry
```

All weights are explicit configuration values.

```text
ADVERSARIAL_SCORE != UNIVERSAL_DIFFICULTY
HIGH_DISCRIMINATION != FAIRNESS
LOW_EFFICIENCY != FUN
```

## Evolution

`evolve_layout_population`:

1. verifies the report exactly covers the layout population;
2. keeps a bounded elite fraction;
3. generates unique valid children by deterministic bounded mutation;
4. records admissions/rejections when evolutionary memory is supplied;
5. fails if the bounded budget cannot fill the requested next population.

This avoids an unbounded retry loop.

## Held-out map sets

R0.8 adds a second and stronger anti-overfitting axis:

```text
training_layout_hashes ∩ validation_layout_hashes = ∅
```

This differs from R0.5 seed holdout. A policy can now be tested on **unseen geometry**, not merely unseen random seeds of the same geometry.

For every agent:

```text
train_mean_quality
validation_mean_quality
generalization_gap
worst_validation_quality
validation_quality_std
```

are reported across distinct map sets.

```text
HELD_OUT_MAPS != REAL_WORLD_GENERALIZATION
SMALL_MAP_GAP != GENERAL_INTELLIGENCE
```

## Deterministic receipts

Layout evaluations and whole reports are content-addressed through canonical SHA-256 receipts over layouts, seeds and measured metrics. Map-generalization reports also hash the exact training/validation layout sets.

## Demo

From `omega_game_t/`:

```bash
PYTHONPATH=. python examples/layout_evolution_demo.py
```

The demo compiles the R0.7 fixed-layout GameSpec, creates a layout population, evaluates it, evolves one generation, constructs a disjoint held-out map set, runs map-generalization measurement, and prints M+/M- evidence.

## OAK boundaries

```text
MUTATION_ADMITTED != BETTER_LEVEL
M_PLUS != PROOF_OF_QUALITY
M_MINUS != PROOF_OF_IMPOSSIBILITY
HELD_OUT_MAPS != REAL_WORLD_GENERALIZATION
ADVERSARIAL_SCORE != UNIVERSAL_DIFFICULTY
GEOMETRIC_FAIRNESS != STRATEGIC_FAIRNESS
EVOLVED_LAYOUT != FUN_GAME
```

## Next

R0.9 should add scalable campaign execution over `(agents × layouts × seeds)` with sharding, checkpoints, backpressure and empirical wall-clock/work-unit comparison before any hardware-speedup claim.
