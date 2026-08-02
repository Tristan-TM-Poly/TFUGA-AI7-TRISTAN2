# Ω-DISCOVERY-KERNEL-T∞ R0.3

## Million-scale forced-resume frontier

**Status:** executable OAKBench architecture. It validates workflow scale,
identity, parentage, sharding, checkpointing, forced interruption and exact
resume. It does not validate a scientific theory, physical model, product,
patent, safety claim or causal explanation.

---

## 1. Why R0.3 exists

R0.1 proved that the discovery loop could be represented:

```text
ObservationEvent
→ ClaimEvent
→ GeneratorCandidate
→ ExperimentSpec
→ ResultPacket
→ OAKTransition
→ MMinusRule
→ ActionProposal
```

R0.2 expanded that proof into:

- 64 canonical event contracts;
- 50,000 full discovery events;
- 50,100 diversified knowledge and GitHub-plan additions;
- 36 benchmark families;
- universal identities;
- quantities and uncertainty;
- adaptive shards and SQLite indexes.

R0.3 attacks the next architectural question:

> Can the system survive a real million-event frontier, be deliberately
> interrupted halfway, resume exactly, preserve lineage and convert every
> observed saturation into reusable negative memory?

The canonical test is:

```text
1,000,000 events
÷ 8 events per complete loop
= 125,000 complete discovery subjects
```

The process is deliberately terminated after:

```text
524,288 events
= 65,536 complete subjects
```

It then resumes from the persisted checkpoint and reaches exactly one million.

The event target is a finite test objective. The architecture contains no
`max_total_events` field and makes no claim of physically infinite execution.

---

## 2. Honest compact representation

Serializing one million full Python dictionaries would spend most of the test
budget repeating identical field names and synthetic fixture text. R0.3
therefore separates:

```text
semantic event templates
+
individual compact records
```

Each compact JSONL line is still one event. Its array contains:

```text
sequence
unique deterministic event ID
event type code
subject index
namespace index
parent sequence
timestamp offset in microseconds
SHA-256 event hash
```

The semantic meaning of codes `0..7`, common provenance, domain, status,
timestamp origin, identity rule and parent rule are stored in
`event-templates.json`.

This is compression of repeated representation, not compression of event
count. The SQLite index contains one row per event.

The schema is:

```text
schemas/compact-discovery-record.schema.json
```

---

## 3. Deterministic identity

For every sequence `s`, subject `q` and event slot `k`, the ID is derived from:

```text
SHA-256("million-frontier", seed, s, q, k)
```

and encoded as:

```text
evt_<24 hexadecimal characters>
```

The record hash is independently calculated from canonical semantic fields.
The full ledger uses a chained digest:

```text
digest[n+1] = SHA256(digest[n] || event_hash[n+1])
```

This enables exact continuation from the stored checkpoint without holding a
million hashes in memory.

The hash proves byte and sequence integrity under the implemented contract. It
does not prove that an event's scientific interpretation is true.

---

## 4. Parent and subject invariants

The eight core slots are:

| Code | Event |
|---:|---|
| 0 | ObservationEvent |
| 1 | ClaimEvent |
| 2 | GeneratorCandidate |
| 3 | ExperimentSpec |
| 4 | ResultPacket |
| 5 | OAKTransition |
| 6 | MMinusRule |
| 7 | ActionProposal |

For every subject:

```text
slot 0 → no parent
slot 1 → parent slot 0
slot 2 → parent slot 1
...
slot 7 → parent slot 6
```

A subject is complete only when:

```text
event_count = 8
AND
core_mask = 0b11111111
```

The final audit requires:

- sequences from `0` to `999,999` with no gap;
- one million distinct event IDs;
- zero missing parents;
- 125,000 subjects;
- 125,000 complete subjects;
- 125,000 M⁻ events;
- the final chained digest;
- a complete checkpoint.

---

## 5. Disk-backed architecture

### JSONL shards

Events are written to adaptive immutable shards:

```text
shards/compact-events-00000000.jsonl
shards/compact-events-00000001.jsonl
...
```

The initial byte calibration is four MiB. Successful rotations increase the
next target by a multiplicative factor. This is a starting calibration, not a
permanent shard or total-volume cap.

### SQLite WAL index

`million-index.sqlite3` stores:

```text
events.sequence
events.event_id
events.event_code
events.subject_index
events.namespace_index
events.parent_sequence
events.timestamp_offset_us
events.event_hash
events.shard_path
events.byte_offset
events.byte_length
```

The subject table stores:

```text
subject index
namespace
event count
core mask
first sequence
last sequence
```

Indexes support event ID, subject and parent lookup.

### Bounded in-process state

The implementation retains only:

- the active shard stream;
- the current SQLite batch;
- a small telemetry object;
- the chained digest;
- checkpoint state.

It does not retain one million event objects in RAM.

---

## 6. Forced interruption

The first phase ends deliberately on a complete-subject boundary:

```text
sequence = 524,288
```

Before termination, the system writes:

- pending SQLite rows;
- the current shard buffer;
- an incomplete checkpoint;
- a forced-interruption saturation record;
- a reusable M⁻ rule;
- a redesign action.

The negative-memory rule is:

> Never infer resumability from a clean uninterrupted run.

The prescribed redesign is:

```text
resume from checkpoint
→ reject duplicates
→ continue sequence exactly
→ verify digest continuity
→ verify all subjects complete
```

The second process opens the existing shard and SQLite index, restores the
next sequence and chained digest, then writes the remaining events.

---

## 7. Saturation-to-M⁻ protocol

R0.3 recognizes four saturation classes.

### Forced interruption

Purpose: prove recovery rather than assume it.

### SQLite batch latency

Trigger: a commit batch crosses the calibrated latency threshold.

M⁻:

> Do not increase batch or index complexity without measuring commit latency.

Possible redesigns:

- reduce batch size;
- repartition indexes;
- separate cold lineage storage;
- shard indexes by namespace or sequence range.

### Resident memory

Trigger: peak resident memory crosses the configured frontier.

M⁻:

> Never trade unbounded RAM growth for throughput.

Possible redesigns:

- reduce cache;
- reduce batch size;
- remove in-memory identity sets;
- use partitioned disk indexes.

### Disk backpressure

Trigger: free disk falls below the rollback and shard-finalization reserve.

M⁻:

> Never continue writing when rollback storage cannot be guaranteed.

Possible redesigns:

- pause and checkpoint;
- expand storage;
- move closed immutable shards;
- compact indexes;
- resume only after the safety reserve is restored.

Every recorded saturation is written to:

```text
saturation-m-minus.jsonl
```

---

## 8. Outputs

```text
event-templates.json
million-index.sqlite3
million-checkpoint.json
million-manifest.json
million-telemetry.json
million-experiment-summary.json
saturation-m-minus.jsonl
shards/*.jsonl
```

### Manifest

The manifest records:

- configuration;
- exact event and subject totals;
- unique IDs;
- duplicate and orphan counts;
- M⁻ event count;
- sequence continuity;
- subject completeness;
- ledger digest;
- shard count;
- telemetry;
- saturation count;
- remote mutation count;
- OAK boundary.

### Telemetry

The telemetry includes:

```text
accepted events
duplicates
rejections
bytes written
shards closed
SQLite commits
checkpoints
forced interruptions
saturation records
elapsed time
events per second
bytes per second
peak resident memory
last batch latency
```

---

## 9. Command

```bash
python -m omega_discovery_kernel_t million-frontier \
  --events 1000000 \
  --interrupt-after 524288 \
  --namespaces 256 \
  --output-dir generated/omega_discovery_kernel_t/frontier-1m-r0-3
```

The command returns nonzero if any of the following is false:

```text
exact target reached
zero duplicate IDs
zero orphan parents
contiguous sequence
all subjects complete
```

---

## 10. What the million events are

They are deterministic synthetic workflow fixtures used to test:

- storage architecture;
- identity stability;
- lineage;
- checkpointing;
- interruption;
- resume;
- deduplication;
- integrity audits;
- negative-memory generation;
- telemetry.

They are not one million independent scientific observations. They are not one
million sources, experiments or external validations.

The correct claim is:

> The software executed and audited one million individually indexed workflow
> events under the compact R0.3 contract.

The prohibited claim is:

> The corpus gained one million units of scientific evidence.

---

## 11. OAK falsification conditions

R0.3 fails its own objective if any of the following occurs:

- final count differs from 1,000,000;
- any sequence is missing;
- any event ID is duplicated;
- any parent is absent;
- any subject lacks one of the eight core events;
- the M⁻ count differs from 125,000;
- resume restarts from zero;
- resumed events overwrite prior events;
- the checkpoint is marked complete before the second phase;
- the interruption produces no M⁻ record;
- the final manifest hides observed saturation;
- the implementation requires loading the full event set into memory.

---

## 12. Next adaptive frontiers

The architecture should not stop at the symbolic milestone of one million.
Subsequent finite experiments should discover the actual saturation curve:

```text
1M
→ 2M
→ 5M
→ 10M
→ first real bottleneck
→ M⁻
→ redesign
→ repeat
```

The next major improvements are:

1. partitioned SQLite indexes by sequence and namespace;
2. content-addressed cold-shard storage;
3. Merkle roots per shard and global frontier root;
4. independent reproduction on another machine;
5. crash injection during shard rotation and SQLite commit;
6. corrupted-checkpoint detection and recovery;
7. concurrent producers with deterministic merge order;
8. real source and dataset events mixed with synthetic fixtures;
9. versioned KnowledgeCell updates from external ResultPackets;
10. proof-density and evidence-quality metrics independent of raw event count.

---

## 13. Final boundary

```text
Scale is not truth.
Hash integrity is not causality.
Resume is not scientific replication.
A million events is not a million proofs.
```

R0.3 demonstrates that Ω-DISCOVERY-KERNEL-T∞ can treat a million workflow
events as a recoverable, indexed and auditable frontier while preserving OAK
restrictions and negative memory.
