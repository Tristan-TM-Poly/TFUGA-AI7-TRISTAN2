# Ω-GAME-SIM-EVO-T∞ R0.12 — Causal Coordinator Ledger

**Status:** executable candidate stacked on R0.11  
**Authority:** local orchestration audit / state-machine evidence only

## Goal

Turn implicit coordinator transitions into an append-only causal evidence chain:

```text
worker register
→ heartbeat
→ shard assign
→ acknowledgement
→ success | failure | lease expiry
→ retry schedule | exhausted
```

Every accepted transition emits a `CoordinatorEvent` whose SHA-256 receipt commits to the previous event receipt.

## Event chain

An event commits to:

```text
version
sequence
kind
plan_receipt
previous_receipt
shard_id
worker_id
attempt
payload
```

```text
event_receipt = SHA256(canonical_event_body)
```

Therefore modifying, dropping or reordering an old event invalidates the chain.

```text
EVENT_CHAIN_INTEGRITY != EXTERNAL_EVENT_TRUTH
```

The ledger proves consistency of the recorded internal history, not that a remote worker actually performed what an event says.

## Supported events

```text
worker_registered
worker_heartbeat
shard_assigned
shard_acknowledged
shard_succeeded
shard_failed
lease_expired
retry_scheduled
```

Unknown kinds fail closed.

## Shard state machine

Current bounded shard states are:

```text
pending
assigned
acked
retry_pending
succeeded
exhausted
```

Allowed core paths include:

```text
pending → assigned → acked → succeeded
pending → assigned → failed → retry_pending → assigned ...
pending → assigned/acked → lease_expired → retry_pending ...
```

When `attempt >= max_attempts`, failure/expiry ends in `exhausted` rather than an unbounded retry loop.

A non-owning worker cannot acknowledge or complete a shard.

## Integration with R0.11

`CampaignCoordinator` composes:

```text
WorkerRegistry
TTLLeaseCoordinator
CoordinatorLedger
ShardCoordinatorState[]
```

Assignment requires a heartbeat-active worker and obtains a TTL lease. The event ledger stores deterministic lease token/epoch identity, not wall-clock issue/expiry timestamps.

Heartbeat events store the logical heartbeat receipt, not the observation timestamp.

Thus identical logical event sequences can have identical event receipts even when executed under different clock origins.

```text
RUNTIME_TIME != DETERMINISTIC_EVENT_IDENTITY
```

## Transition validation before append

Illegal transitions raise before an event is appended. Examples:

- duplicate acknowledgement;
- success before acknowledgement;
- acknowledgement by the wrong worker;
- assignment from a terminal shard;
- assignment beyond the retry budget;
- heartbeat for an unregistered worker.

This prevents the ledger from recording an invalid state transition as though it were accepted.

## Replay audit

`replay_coordinator_events` reconstructs shard state from the event chain without using the live mutable coordinator state.

`CampaignCoordinator.audit()`:

1. validates SHA-256 causal chaining;
2. replays all events under the same manifest and retry bound;
3. compares replayed shard state against live state.

A mismatch becomes an audit flag rather than being silently reconciled.

## Failure and expiry evidence

Failures record a supplied failure receipt from the runtime layer. Lease expiry records lease token and epoch. Retry scheduling records the next bounded attempt and reason.

```text
FAILURE_RECEIPT != ROOT_CAUSE_PROOF
LEASE_EXPIRY_EVENT != PROOF_WORKER_IS_DEAD
```

## Demo

From `omega_game_t/`:

```bash
PYTHONPATH=. python examples/campaign_coordinator_demo.py
```

The demo records two worker lifecycles: one successful shard and one exhausted failure, then validates the ledger and state replay.

## OAK boundaries

```text
EVENT_CHAIN_INTEGRITY != EXTERNAL_EVENT_TRUTH
COORDINATOR_LEDGER != DISTRIBUTED_CONSENSUS
WORKER_ACK != REMOTE_ATTESTATION
LEASE_EXPIRY_EVENT != PROOF_WORKER_IS_DEAD
FAILURE_RECEIPT != ROOT_CAUSE_PROOF
REPLAY_EQUIVALENCE != SCIENTIFIC_VALIDITY
```

## Next

R0.13 should connect campaign results back into the evolutionary selection loop as a typed ExperimentGraph: jobs, layouts, agents, seeds, receipts, coordinator events, M+/M- and selection decisions become one provenance graph. The objective is not more orchestration machinery, but end-to-end evidence from generated candidate to promoted descendant.
