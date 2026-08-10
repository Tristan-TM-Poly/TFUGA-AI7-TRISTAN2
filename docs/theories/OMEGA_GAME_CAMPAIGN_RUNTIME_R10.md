# Ω-GAME-SIM-EVO-T∞ R0.10 — Persisted Process Campaign Runtime

**Status:** executable candidate stacked on R0.9  
**Authority:** local/process orchestration and benchmark evidence only

## Runtime loop

```text
CampaignManifest
→ deterministic shards
→ controller-local leases
→ bounded attempts
→ process workers
→ shard checkpoints
→ merge
→ atomic persisted checkpoint artifact
→ resume
→ empirical sequential/process comparison
```

## Persistence

R0.10 introduces versioned `CheckpointArtifact 0.1`.

A saved artifact contains:

```text
version
plan_receipt
checkpoint_receipt
completed job result objects
```

Writing uses:

```text
write temporary file
→ flush
→ fsync
→ os.replace(target)
```

The returned persistence receipt records the content SHA-256, byte count and deterministic checkpoint receipt.

Loading reparses every `CampaignResult`, validates its result receipt, verifies the plan binding and recomputes the checkpoint receipt.

```text
FILE_EXISTS != VALID_CHECKPOINT
CONTENT_HASH != SCIENTIFIC_TRUTH
```

## Logical leases

`LeaseLedger` prevents the controller from intentionally assigning the same shard twice at once.

A lease token hashes:

```text
plan_receipt
shard_id
worker_id
attempt
```

This is a controller-local orchestration lock.

```text
LEASE_LEDGER != DISTRIBUTED_CONSENSUS
LEASE_TOKEN != GLOBAL_EXCLUSIVE_LOCK
```

There is no cross-host quorum, TTL consensus or split-brain protocol in R0.10.

## Bounded retries and failure evidence

`run_process_shards` has finite `max_attempts`.

Worker exceptions become `ShardFailureReceipt` objects containing:

```text
shard_id
attempt
worker_id
error_type
SHA256(error message)
failure_receipt
```

The raw error message is not embedded in the failure receipt object, reducing accidental propagation of sensitive strings while preserving stable evidence identity.

Failed shards are retried only up to the explicit attempt bound.

## Process execution

For `workers > 1`, R0.10 uses `ProcessPoolExecutor` to run independent deterministic shards. Each child receives the same immutable campaign manifest and executes one shard through the R0.9 engine.

Successful shard checkpoints are merged using the existing conflict gate.

Correctness criterion:

```text
checkpoint_receipt(process workers=N)
==
checkpoint_receipt(workers=1)
```

for the exact same complete deterministic campaign.

## Empirical speed comparison

`compare_process_execution` runs the same manifest once with one worker and once with the requested process count.

It reports:

```text
sequential_wall_clock_seconds
process_wall_clock_seconds
observed_speedup = sequential / process
```

but first requires deterministic checkpoint equivalence.

The speedup is an observed sample and may be less than one because of process startup, IPC, workload size, machine contention or runtime effects.

```text
OBSERVED_SPEEDUP != GUARANTEED_SPEEDUP
PROCESS_COUNT != SPEEDUP
DETERMINISTIC_EQUIVALENCE != PERFORMANCE_EQUIVALENCE
```

Wall-clock values are not inserted into deterministic campaign/checkpoint receipts.

## Demo

From `omega_game_t/`:

```bash
PYTHONPATH=. python examples/campaign_runtime_demo.py
```

The demo:

1. plans a finite campaign;
2. executes a backpressured slice;
3. atomically saves the checkpoint;
4. loads and validates it;
5. resumes another slice;
6. compares one-worker and two-process complete executions;
7. requires identical deterministic checkpoint receipts.

## OAK boundaries

```text
LEASE_LEDGER != DISTRIBUTED_CONSENSUS
ATOMIC_LOCAL_REPLACE != REMOTE_DURABILITY
RETRY_SUCCESS != ROOT_CAUSE_RESOLUTION
PROCESS_COUNT != SPEEDUP
OBSERVED_SPEEDUP != GUARANTEED_SPEEDUP
CHECKPOINT_HASH != EXTERNAL_CERTIFICATION
DETERMINISTIC_EQUIVALENCE != SCIENTIFIC_VALIDITY
```

## Next

R0.11 can add explicit worker manifests, heartbeat/TTL adapters, remote artifact-store interfaces and resumable campaign bundles, but any true distributed lease/consensus claim must be validated against a real coordination backend rather than inferred from this local controller model.
