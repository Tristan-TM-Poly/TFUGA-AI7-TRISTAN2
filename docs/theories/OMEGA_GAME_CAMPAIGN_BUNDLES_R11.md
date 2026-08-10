# Ω-GAME-SIM-EVO-T∞ R0.11 — Campaign Bundles, Worker Registry and Content-Addressed Artifacts

**Status:** executable candidate stacked on R0.10  
**Authority:** local coordination / portable experiment packaging only

## Bundle loop

```text
CampaignManifest + optional Checkpoint + WorkerManifests
→ CampaignBundle
→ bundle_receipt
→ content-addressed artifact store
→ restore
→ validate plan/checkpoint
→ heartbeat / local TTL lease
→ resume exact campaign
```

## CampaignBundle

`CampaignBundle 0.1` packages enough deterministic state to reconstruct the experiment without retaining the original Python objects:

```text
version
full CampaignManifest payload
optional CheckpointArtifact
normalized WorkerManifest list
bundle_receipt
```

Restore reconstructs:

- normalized `AgentGenome` objects;
- fixed `ArenaLayout` objects;
- `ArenaConfig`;
- every `CampaignJob`;
- every `CampaignShard`;
- the exact `plan_receipt`;
- optional validated checkpoint;
- worker manifests.

The reconstructed manifest passes the R0.9 manifest validation again.

```text
BUNDLE_RECEIPT != EXTERNAL_CERTIFICATION
RESTORED_OBJECT != SCIENTIFIC_TRUTH
```

## Worker manifests

A worker declares a bounded protocol contract:

```text
worker_id
protocol_version
max_concurrent_shards
tags[]
```

The normalized manifest is content-addressed by `manifest_receipt`.

These are self-declared orchestration capabilities, not hardware attestation.

```text
WORKER_MANIFEST != HARDWARE_ATTESTATION
```

## Heartbeats

`WorkerRegistry` records heartbeats against an injectable clock.

Each heartbeat has:

```text
worker_id
logical sequence
observed_at runtime timestamp
manifest_receipt
heartbeat_receipt
```

The deterministic heartbeat receipt hashes worker ID, sequence and manifest identity but intentionally excludes `observed_at`.

Thus two identical logical first heartbeats can share receipt identity even if observed at different wall/monotonic times.

```text
OBSERVATION_TIME != DETERMINISTIC_PROVENANCE
```

## TTL shard leases

`TTLLeaseCoordinator` adds local expiration and reassignment semantics on top of R0.10 logical leases.

Acquisition requires:

- worker registered;
- recent heartbeat under `heartbeat_ttl_seconds`;
- no unexpired lease for the shard.

Each reassignment increments a shard-local epoch. Lease token identity hashes:

```text
plan_receipt
shard_id
worker_id
epoch
```

Runtime fields `issued_at` / `expires_at` are excluded from the token.

Expired leases can be removed and the shard reassigned at the next epoch.

```text
TTL_LEASE_COORDINATOR != DISTRIBUTED_CONSENSUS
LEASE_EXPIRY != PROOF_WORKER_IS_DEAD
```

Clock skew, process pauses, network partitions and split-brain coordination are outside this local controller prototype.

## Content-addressed artifact store

R0.11 defines the small `ArtifactStore` protocol:

```text
put_bytes(data, media_type) -> ArtifactReceipt
get_bytes(receipt) -> bytes
```

`LocalContentAddressedStore` implements it locally using:

```text
SHA256(content)
→ <root>/<sha-prefix>/<sha>
```

Writes use temporary-file + flush + fsync + replace. Reads verify byte count and SHA-256 before returning content.

Identical bytes deduplicate to the same content path.

```text
LOCAL_CAS != REMOTE_DURABILITY
CONTENT_ADDRESS != BACKUP
```

The protocol surface is intentionally small so a future authorized remote store can implement the same contract without changing bundle semantics.

## Portable resume

A partial campaign can now follow:

```text
plan
→ execute slice
→ checkpoint
→ CampaignBundle
→ CAS
→ reload bytes
→ verify bundle receipt
→ reconstruct manifest/checkpoint
→ resume
→ same final checkpoint receipt as direct execution
```

This is the core R0.11 invariant.

## Demo

From `omega_game_t/`:

```bash
PYTHONPATH=. python examples/campaign_bundle_demo.py
```

The demo exercises partial execution, bundle creation, local CAS, restore, worker registration, heartbeat, TTL lease/release and final resumed equivalence against a direct run.

## OAK boundaries

```text
WORKER_MANIFEST != HARDWARE_ATTESTATION
HEARTBEAT != PROOF_OF_HEALTH
TTL_LEASE_COORDINATOR != DISTRIBUTED_CONSENSUS
LEASE_EXPIRY != PROOF_WORKER_IS_DEAD
LOCAL_CAS != REMOTE_DURABILITY
CONTENT_ADDRESS != BACKUP
BUNDLE_RECEIPT != EXTERNAL_CERTIFICATION
RESUME_EQUIVALENCE != SCIENTIFIC_VALIDITY
```

## Next

R0.12 can implement an explicit distributed-simulation adapter contract and a local multi-worker coordinator state machine with assignment/ack/failure event receipts. True cross-host guarantees should only be claimed after running against a real external coordination/storage backend and fault-injection tests.
