# Ω-PROBLEM-ATLAS-T∞ R0.10

## Streaming, SQLite WAL and scale without a permanent ceiling

R0.10 replaces the finite in-memory materialization path with a streaming,
transactional and resumable storage layer.

```text
JSONL / deterministic generator / R0.3 MAX
  -> strict cell validation
  -> bounded batches
  -> SQLite WAL transaction
  -> duplicate or quarantine ledger
  -> streaming Merkle accumulator
  -> deterministic byte-target shards
  -> checkpoint
  -> logical manifest
  -> replay audit
```

## Core distinction

```text
no permanent total cap != infinite resources
```

R0.10 does not encode a `max_total_cells` or equivalent permanent ceiling.
Each run remains constrained by real resources:

- available disk;
- SQLite and filesystem limits;
- process memory;
- runtime;
- CI budgets;
- operating-system limits;
- user-selected batch and shard sizes.

Every report therefore fixes:

```json
{
  "permanent_total_cell_cap": null,
  "unlimited_capacity_claimed": false,
  "peak_memory_independent_of_total_claimed": false
}
```

A completed 100k or 1M benchmark is a finite measurement, not proof of
unlimited capacity.

## Commands

### Stream JSONL

```bash
omega-problem-stream ingest \
  --input-jsonl campaigns/cells.jsonl \
  --output-dir generated/stream_r10 \
  --batch-size 1000 \
  --shard-target-bytes 8388608
```

### Interrupt intentionally

```bash
omega-problem-stream ingest \
  --input-jsonl campaigns/cells.jsonl \
  --output-dir generated/stream_r10 \
  --batch-size 1000 \
  --max-items 25000
```

### Resume

```bash
omega-problem-stream ingest \
  --input-jsonl campaigns/cells.jsonl \
  --output-dir generated/stream_r10 \
  --batch-size 1000 \
  --resume \
  --no-clean
```

The source SHA-256 and runtime policy must match the checkpoint exactly.

### Deterministic synthetic campaign

```bash
omega-problem-stream synthetic \
  --output-dir generated/synthetic_r10 \
  --cell-count 1000000 \
  --batch-size 2000
```

This command generates cells lazily. `cell_count` describes a finite campaign,
not a permanent product limit.

### R0.3 MAX compatibility

```bash
omega-problem-stream verify-r03 generated/omega_problem_atlas_r03_max

omega-problem-stream r03-max \
  --source-dir generated/omega_problem_atlas_r03_max \
  --output-dir generated/r03_stream_r10
```

### Bounded portfolio query

```bash
omega-problem-stream query generated/stream_r10 \
  --limit 24 \
  --max-per-front 2 \
  --min-priority 100
```

The query executes in SQLite using a window function. It does not load the full
atlas into Python.

### Audit

```bash
omega-problem-stream audit generated/stream_r10
```

### Finite benchmark

```bash
omega-problem-stream benchmark \
  --output-dir generated/stream_benchmark_r10 \
  --sizes 10000 100000 1000000
```

The benchmark records Python peak memory with `tracemalloc`, database bytes and
elapsed time. It explicitly reports `bounded_memory_proven: false` because a
finite sample does not prove an asymptotic theorem.

## Cell contract

Each JSONL row contains:

- stable `cell_id`;
- `problem_id`;
- `target_id`;
- front;
- method;
- integer routing priority;
- source reference;
- arbitrary JSON object payload.

Unknown top-level fields fail cell validation and enter quarantine. Invalid
rows do not disappear silently.

## SQLite schema

R0.10 stores:

- `cells` — canonical unique cells and their digests;
- `duplicates` — exact duplicates and ID collisions;
- `quarantine` — invalid or conflicting rows;
- `checkpoints` — crash-safe streaming state;
- `shards` — deterministic logical shard receipts;
- `rollback_receipts` — failed-batch evidence;
- `metadata` — schema and compatibility receipts.

Important indexes cover:

- problem identity;
- target identity;
- `(front, priority, cell_id)` portfolio ranking.

SQLite runs with:

```text
journal_mode = WAL
synchronous = FULL
foreign_keys = ON
bounded busy timeout
```

## Transaction model

A batch contains at most `batch_size` records.

Within one transaction, R0.10:

1. validates rows;
2. inserts cells or ledgers;
3. updates Merkle state;
4. updates shard state;
5. enforces the runtime disk budget;
6. writes the checkpoint;
7. commits.

If any operation raises, SQLite rolls back and the in-memory checkpoint state
is restored to the pre-batch copy. A rollback receipt is then appended in a
separate committed transaction.

## Duplicate policy

### Exact duplicate

Same `cell_id`, same canonical cell digest:

- canonical cell remains unchanged;
- duplicate receipt is appended;
- sequence and Merkle leaf count do not increase.

### Conflicting duplicate

Same `cell_id`, different digest:

- canonical cell remains unchanged;
- duplicate receipt is appended;
- conflicting row enters quarantine;
- no implicit overwrite occurs.

## Quarantine

Quarantine preserves:

- source ordinal;
- optional cell ID;
- reason;
- digest of the raw input;
- bounded raw excerpt;
- receipt digest.

Malformed JSON interrupts the generator before it can be treated as a valid
row. The active batch is rolled back and a rollback receipt records the
failure. Structurally invalid JSON objects are quarantined and streaming
continues.

## Checkpoint

The checkpoint binds:

- source kind and digest;
- next source ordinal;
- next canonical sequence;
- input, inserted, duplicate and quarantine counts;
- complete/incomplete state;
- global Merkle peaks;
- active shard state;
- exact runtime policy.

Resume fails closed if source content or runtime policy changes.

## Merkle accumulator

R0.10 uses a streaming binary peak accumulator. It stores at most logarithmic
Merkle peak state rather than all leaf digests in memory.

Each canonical inserted cell contributes exactly one leaf. Duplicates and
quarantined records do not modify the canonical Merkle root.

## Logical shards

Shards close before an inserted record would make their canonical serialized
byte count exceed `shard_target_bytes`.

Each shard records:

- first and last canonical sequence;
- row count;
- canonical byte count;
- shard Merkle root;
- shard receipt digest.

The final active shard closes only when the campaign reaches completion. This
allows interruption and resume to produce the same final shard boundaries and
manifest as an uninterrupted campaign.

## R0.3 MAX digest bridge

The R0.3 compatibility verifier reads the original:

- `sources.jsonl`;
- `problems.jsonl`;
- `research_targets.jsonl`;
- `research_cells.jsonl`;
- `hyperedges.jsonl`;
- `methods.jsonl`;
- `portfolio.json`;
- `manifest.json`;
- `report.json`.

It then:

1. verifies the R0.3 manifest schema;
2. recomputes every artifact SHA-256, byte count and JSONL row count;
3. recomputes the canonical R0.3 manifest digest;
4. recomputes the canonical R0.3 report digest;
5. verifies the 72-problem and research-cell count contracts;
6. rejects proof, solution, validation and current-status claims;
7. records the exact seven artifact receipts;
8. streams `research_cells.jsonl` into R0.10;
9. embeds the compatibility receipt into the R0.10 manifest.

R0.10 reports:

```text
r03_manifest_digest_reproduced
r03_report_digest_reproduced
```

These fields mean the supplied R0.3 materialization's digests were reproduced.
They do not certify the mathematical truth of its contents.

## Portfolio query

R0.10 ranks cells per front using:

```sql
ROW_NUMBER() OVER (
  PARTITION BY front
  ORDER BY priority DESC, cell_id ASC
)
```

Then it applies `max_per_front` and a global limit. This keeps query memory
bounded by the returned portfolio plus SQLite's own execution resources.

## Audit

The replay audit verifies:

- checkpoint digest;
- contiguous canonical sequence;
- every canonical cell digest;
- global Merkle leaf count and root;
- duplicate receipts;
- quarantine receipts;
- rollback receipts;
- shard digests, sequence ranges and Merkle roots;
- logical manifest replay;
- manifest and report digests;
- R0.3 compatibility receipt binding when present;
- null permanent cap;
- absence of unlimited-capacity claims.

SQLite file bytes are not used as the canonical scientific digest. SQLite may
change internal page layout, WAL state or vacuum representation without
changing the logical atlas. The canonical objects are cells, receipts, Merkle
roots and the logical manifest.

## Scale validation

The automated matrix uses moderate finite campaigns to remain compatible with
normal CI budgets. A separate scale job can materialize 100k cells. A one
million-cell run is available through workflow dispatch or local execution.

For every size, report:

- campaign size;
- completion status;
- logical manifest digest;
- SQLite bytes;
- measured Python peak memory;
- elapsed time;
- finite benchmark disclaimer.

Do not transform these observations into a proof that memory is universally
independent of total cell count.

## OAK status

`CERTIFIED_STREAMING_SQLITE_FIXTURE_R0_10` may certify deterministic logical
materialization, resume equivalence and audit behavior for supplied finite
fixtures after CI succeeds.

It does not certify:

- infinite capacity;
- unlimited hardware;
- asymptotic memory complexity;
- mathematical correctness of cell content;
- current open status;
- proof or solution of any problem.
