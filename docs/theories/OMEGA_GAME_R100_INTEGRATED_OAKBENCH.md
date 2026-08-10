# Ω-GAME-SIM-EVO-T∞ R1.0 — Integrated OAKBench

**Status:** consolidation candidate after R0.1–R0.13  
**Authority:** local executable evidence / review support only

## Purpose

R1.0 intentionally stops adding abstraction layers and asks a harder question:

> Do the previously built simulation, geometry, evolution, campaign, persistence, coordinator and provenance layers work together under one reproducible experiment with explicit fault injection?

The integrated loop is:

```text
GameSpec
→ fixed ArenaLayout
→ deterministic Arena-T0
→ match audit
→ valid layout population
→ held-out map generalization
→ deterministic campaign plan
→ campaign checkpoint
→ bundle + local CAS restore
→ coordinator ledger
→ ExperimentGraph + M+/M- + selection decision
→ process equivalence check
→ fault injection matrix
→ capability report
```

## Deterministic vs empirical channels

The R1.0 report deliberately separates two channels.

### Deterministic provenance

The final `deterministic_receipt` hashes:

```text
benchmark config
accepted flag
invariant checks
content/provenance receipts
fault-injection detection results
capability matrix
```

### Empirical observations

The following are reported but excluded from the deterministic receipt:

```text
empirical_timings_seconds
observed_process_speedup
```

This preserves the distinction:

```text
DETERMINISTIC_PROVENANCE != WALL_CLOCK
OBSERVED_SPEEDUP != GUARANTEED_SPEEDUP
```

## Integrated invariants

R1.0 checks that:

- the fixed GameSpec compiles and is OAK accepted;
- the same fixed-layout match reproduces the same replay hash;
- the match audit passes;
- the match carries the expected layout hash;
- training and validation layout hashes are disjoint;
- the finite campaign completes;
- bundle restore preserves the campaign plan receipt;
- bundle restore preserves the checkpoint receipt;
- coordinator ledger/state replay audit passes;
- ExperimentGraph audit passes;
- the selection evidence closure contains result evidence;
- the selection evidence closure contains checkpoint evidence;
- process execution produces the same deterministic checkpoint as one-worker execution;
- every fault in the declared fault matrix is detected.

The integrated benchmark is accepted only when all declared invariants are true.

## Fault-injection matrix

R1.0 actively injects failures rather than only exercising happy paths.

Current matrix:

```text
replay_hash_tamper
→ audit_match

invalid/disconnected_layout
→ ArenaLayout.audit

checkpoint_result_tamper
→ CampaignCheckpoint.validate_for

bundle_manifest_tamper
→ CampaignBundle.from_dict

CAS_content_tamper
→ LocalContentAddressedStore.get_bytes

coordinator_event_tamper
→ CoordinatorLedger.validate_chain

selection_missing_evidence
→ ExperimentGraph.audit

held_out_layout_leakage
→ evaluate_map_generalization

wrong_worker_ack
→ CampaignCoordinator ownership gate
```

A detected injected fault means the tested detector rejected that specific perturbation.

```text
FAULT_DETECTED != ALL_FAULTS_COVERED
```

No finite fault matrix proves the absence of other failure classes.

## Capability matrix

R1.0 records explicit capability status instead of allowing architectural vocabulary to inflate into claims.

### Demonstrated locally

The matrix marks R0.1–R0.13 local executable capabilities as `demonstrated_local`, including deterministic simulation, sparse scheduling, quality diversity, evolutionary memory, coevolution, GameSpec compilation, fixed layouts, layout evolution, checkpointed campaigns, local process execution, local bundles/CAS/TTL coordination, causal coordinator ledger and ExperimentGraph evidence closure.

Each demonstrated row also carries a boundary describing what the evidence does **not** establish.

### Not demonstrated

The following remain explicitly `not_demonstrated`:

```text
distributed consensus
remote durable artifact storage
guaranteed multi-process speedup
strategic fairness / fun / general intelligence
```

They must not be promoted merely because adjacent local abstractions exist.

## R0.1 → R0.13 consolidation map

```text
R0.1  deterministic simulation / tournament / evolution
R0.2  sparse-event scheduling / Temporal LOD / CostGraph
R0.3  MAP-Elites quality diversity
R0.4  Hall of Fame + M+/M-
R0.5  agent↔environment coevolution + held-out seeds
R0.6  bounded GameSpec compiler
R0.7  fixed hashed layouts
R0.8  adversarial layout evolution + held-out maps
R0.9  deterministic sharded campaign engine
R0.10 checkpoint persistence + local process runtime
R0.11 campaign bundles + heartbeat/TTL + local CAS
R0.12 causal coordinator ledger
R0.13 ExperimentGraph + selection evidence closure
R1.0   integrated OAKBench + fault matrix + capability status
```

## Demo

From `omega_game_t/`:

```bash
PYTHONPATH=. python examples/integrated_oakbench_demo.py
```

The command exits non-zero when the integrated report is not accepted.

## OAK boundaries

```text
INTEGRATED_PASS != SCIENTIFIC_TRUTH
FAULT_DETECTED != ALL_FAULTS_COVERED
LOCAL_DEMONSTRATION != DISTRIBUTED_GUARANTEE
OBSERVED_SPEEDUP != GUARANTEED_SPEEDUP
PROVENANCE_CLOSURE != LOGICAL_PROOF
CAPABILITY_STATUS != EXTERNAL_CERTIFICATION
DETERMINISTIC_EQUIVALENCE != PHYSICAL_VALIDITY
BENCHMARK_SELECTION != GENERAL_INTELLIGENCE
GEOMETRIC_FAIRNESS != STRATEGIC_FAIRNESS
```

## Promotion criterion

R1.0 should be promoted only after:

```text
full omega_game_t pytest suite passes
AND integrated demo exits 0
AND GitHub omega-game-t-ci is green
```

After R1.0, priority should shift to hardening and empirical benchmarking rather than immediately adding another architectural layer. Known hardening targets include serialization round-trips, retry-state replay equivalence, broader fault injection, profiling and stronger package/CLI surfacing.
