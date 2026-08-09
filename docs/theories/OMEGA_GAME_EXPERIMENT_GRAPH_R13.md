# Ω-GAME-SIM-EVO-T∞ R0.13 — ExperimentGraph / Evidence Closure

**Status:** executable candidate stacked on R0.12  
**Authority:** provenance, evidence routing and review support only

## Goal

Close the loop between generation, simulation, orchestration, memory and selection:

```text
agent / layout candidate
→ campaign job
→ seed + geometry
→ replay/result receipt
→ checkpoint
→ coordinator event history
→ M+ / M-
→ selection decision
→ evidence closure
```

R0.13 does not invent a new fitness function. It records the evidence dependencies around whatever explicit selection policy is being tested.

## Typed graph

`ExperimentGraph` contains content-addressed nodes and edges.

Current node kinds include:

```text
agent
layout
seed
shard
job
result
checkpoint
worker
coordinator_event
memory_plus
memory_minus
selection_decision
```

Edges include:

```text
left_agent / right_agent
uses_seed
uses_layout
contains_job
produces_result
included_in_checkpoint
causal_predecessor
orchestration_event
worker_event
recorded_in_memory
selection_subject
supports_decision
```

Each node and edge has its own canonical SHA-256 receipt. The entire graph has a `graph_receipt` over sorted node/edge representations.

```text
GRAPH_RECEIPT != SCIENTIFIC_TRUTH
```

## Campaign lowering

`build_campaign_experiment_graph` consumes the exact R0.9 campaign manifest and optional R0.9 checkpoint.

It creates:

- one node per normalized agent;
- one node per fixed layout;
- one node per seed;
- one node per shard;
- one node per job;
- one node per completed result;
- an optional checkpoint node.

Job dependencies are explicit, so a result can be traced back to the exact agents, seed, layout and shard that produced it.

## Coordinator provenance

An optional R0.12 `CoordinatorLedger` is validated before ingestion.

Each coordinator event becomes a graph node with `event_receipt` evidence. Consecutive events are linked by `causal_predecessor`. Shard and worker nodes point to their orchestration events.

Thus orchestration provenance can coexist with scientific/gameplay result provenance without being mistaken for result truth.

## M+ / M- routing

R0.13 accepts an explicit memory payload with `plus` and `minus` sections.

Each memory record becomes a content-addressed node. String references that match known agent IDs, layout hashes, job IDs or result/checkpoint/event receipts are linked with `recorded_in_memory` edges.

```text
M_PLUS != PROOF_OF_TRUTH
M_MINUS != PROOF_OF_IMPOSSIBILITY
```

Memory is retained as evidence/history, not promoted to theorem status.

## SelectionDecision

A decision explicitly declares:

```text
decision_id
subject_node_id
action = retain | promote | quarantine | archive
evidence_receipts[]
score_components{}
rationale_code
```

A selection decision must cite at least one evidence receipt.

When the graph contains a cited receipt, the corresponding evidence node is connected to the decision by `supports_decision`.

If a cited receipt is absent, graph construction can still preserve the proposed decision, but `ExperimentGraph.audit()` rejects it with:

```text
missing_decision_evidence:<decision-node>
```

Therefore:

```text
HIGH_SCORE + MISSING_EVIDENCE → NOT OAK-ACCEPTED
```

## Evidence closure

`evidence_closure(decision_node)` follows incoming edges recursively.

For a supported decision this can recover a chain such as:

```text
agent
seed
layout
job
result
checkpoint
M+ / M-
coordinator events
→ decision
```

This is a provenance closure, not a proof closure in the mathematical sense.

```text
PROVENANCE_CLOSURE != LOGICAL_PROOF
```

## Integrity gates

Graph validation checks:

- node key/ID consistency;
- node receipt recomputation;
- no dangling edge endpoints;
- edge receipt recomputation;
- duplicate edge receipts;
- decision evidence coverage during audit.

Conflicting definitions of the same `node_id` fail closed rather than silently overwriting provenance.

## Demo

From `omega_game_t/`:

```bash
PYTHONPATH=. python examples/experiment_graph_demo.py
```

The demo executes a campaign, creates coordinator evidence, injects M+/M-, creates an evidence-backed retain decision, validates the graph and prints the exact evidence closure plus `graph_receipt`.

## OAK boundaries

```text
GRAPH_RECEIPT != SCIENTIFIC_TRUTH
PROVENANCE_CLOSURE != LOGICAL_PROOF
M_PLUS != PROOF_OF_TRUTH
M_MINUS != PROOF_OF_IMPOSSIBILITY
MANY_SUPPORT_EDGES != HIGHER_TRUTH_PROBABILITY
SELECTION_DECISION != GENERAL_OPTIMALITY
CHECKPOINT_COMPLETION != GENERALIZATION
```

## Resulting Ω-GAME-SIM-EVO chain

R0.1–R0.13 now form a coherent executable ladder:

```text
R0.1 deterministic simulation/tournament/evolution
R0.2 sparse/event scheduling
R0.3 MAP-Elites quality diversity
R0.4 Hall of Fame + M+/M-
R0.5 agent↔environment coevolution
R0.6 GameSpec compiler
R0.7 fixed hashed layouts
R0.8 adversarial layout evolution + held-out maps
R0.9 deterministic sharded campaign engine
R0.10 persisted/process runtime
R0.11 portable bundles + heartbeats/TTL/CAS
R0.12 causal coordinator ledger
R0.13 ExperimentGraph + selection evidence closure
```

The next useful step should be consolidation and benchmarking across this full ladder rather than immediately adding another abstraction layer: package-level exports/CLI, one integrated end-to-end OAKBench, performance profiles, failure injection, and documentation of which parts are demonstrated versus merely architectural.
