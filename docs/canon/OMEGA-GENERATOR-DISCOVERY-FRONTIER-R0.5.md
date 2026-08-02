# Ω-GENERATOR-DISCOVERY FRONTIER R0.5

## Virtual distributed campaigns from 10 billion to quadrillion-scale logical records

**Status:** executable OAK-safe research infrastructure.

R0.5 can describe and coordinate extremely large finite workloads without
materializing every epoch, partition, record, file, commit, or GitHub Actions
matrix entry. A logical cardinality is not an assertion that all records have
been emitted, validated, stored, reviewed, or proven useful.

## 1. Why R0.5 exists

R0.3 established a deterministic campaign with:

- 131,072 generator candidates;
- 1,048,576 linked synthetic benchmarks;
- 1,179,648 logical records.

R0.4 generalized that campaign into multiple content-distinct epochs and
validated plans up to 1,179,648,000 logical records.

At still larger scales, a planner that creates one Python object for every
epoch and partition becomes the next artificial ceiling. R0.5 removes that
materialization requirement.

```text
target cardinality
    ↓
analytical O(1)-memory plan
    ↓
direct partition address
    ↓
bounded page / bounded wave
    ↓
transactional lease
    ↓
streamed generation
    ↓
Merkle-Mountain-Range receipt
    ↓
validation + OAK promotion gate
    ↓
M⁺ breakthrough or M⁻ saturation
```

The architecture remains physically bounded on every execution. It does not
pretend that compute, storage, time, money, API quotas, review capacity,
security, or experimental evidence are infinite.

## 2. Integrated profiles

The CLI exposes convenient finite workloads:

| Profile | Requested logical records |
|---|---:|
| `ten-billion` | 10,000,000,000 |
| `hundred-billion` | 100,000,000,000 |
| `trillion` | 1,000,000,000,000 |
| `ten-trillion` | 10,000,000,000,000 |
| `quadrillion` | 1,000,000,000,000,000 |

An arbitrary positive integer can be supplied through `--target-records`.
Profiles are workload names, not permanent maximums.

## 3. O(1)-memory virtual plan

`VirtualFrontierPlan` stores only analytical quantities:

- campaign identity and fingerprint;
- generator bundles per epoch;
- records per bundle;
- requested and rounded cardinality;
- complete epoch count;
- tail epoch size;
- bundles per partition;
- complete-epoch partition count;
- tail partition count;
- total partition count;
- policy and plan fingerprint.

It deliberately does **not** store:

- a tuple containing every epoch;
- a tuple containing every partition;
- a matrix containing every GitHub job;
- generated payloads;
- validation results that have not been produced.

The memory required by the plan is therefore independent of whether the target
contains one million, one trillion, or one quadrillion logical records.

## 4. Direct addressing

Any epoch or partition can be addressed without iterating through previous
ones.

```python
partition = plan.partition_at(8_000_000_000)
epoch = plan.epoch_at(700_000_000)
```

Partition coordinates include:

- global partition index;
- epoch index;
- local partition index;
- generator start and stop;
- bundle count;
- logical record count;
- suggested shard count;
- content-bound partition key.

The partition key incorporates the plan fingerprint and exact coordinates. It
is stable inside the plan and collision-resistant across distinct plans.

## 5. Pages instead of giant matrices

GitHub Actions, APIs, dashboards, and workers consume bounded pages:

```bash
omega-generator-frontier page \
  --profile trillion \
  --cursor 9000000 \
  --limit 128
```

The response contains:

- the requested cursor;
- at most the requested number of entries;
- the next cursor;
- a completion flag;
- no record payload.

This allows recursive dispatch:

```text
page 0 → validate → dispatch
page 1 → validate → dispatch
...
M⁻ saturation → redesign page policy
M⁺ stability → enlarge wave budget
```

A million-partition campaign never requires a million-entry YAML matrix.

## 6. Adaptive multi-resource scheduler

Logical record count alone is not a safe execution budget. R0.5 evaluates all
of the following simultaneously:

- logical records;
- bytes written;
- estimated compute nanoseconds;
- cost microunits;
- API calls;
- files;
- commits.

`AdaptiveWaveScheduler` selects the largest contiguous partition wave that
fits every supplied constraint.

```bash
omega-generator-frontier schedule \
  --profile trillion \
  --cursor 0 \
  --max-records 50000000 \
  --max-bytes 40000000000 \
  --max-seconds 1800 \
  --max-cost-microunits 50000000 \
  --max-api-calls 10000 \
  --max-files 1000 \
  --max-commits 20
```

The scheduler returns `scheduled`, `blocked`, or `complete`. When blocked it
identifies the limiting dimensions rather than silently truncating the work.

These budgets are backpressure controls. They are not a global cap.

## 7. Streaming Merkle Mountain Range

A conventional Merkle tree often stores all leaves or an entire tree. R0.5
uses a Merkle Mountain Range accumulator:

- append-only;
- deterministic;
- order-sensitive;
- SHA-256 based;
- O(log n) retained hashes;
- suitable for streamed records and partition receipts.

Leaf hashing uses domain separator `0x00`, binary node hashing uses `0x01`,
and peak bagging uses `0x02`.

```bash
omega-generator-frontier mmr-demo --leaves 1000000
```

The output proves byte-level stream integrity and order. It does **not** prove
scientific truth, novelty, correctness of a physical model, or safety.

## 8. Receipt chain

Every completed partition can produce a `FrontierReceipt` containing:

- plan fingerprint;
- partition key;
- worker identity;
- logical records;
- generator bundles;
- MMR root;
- leaf count;
- validation status;
- previous receipt hash;
- completion timestamp;
- receipt hash.

The previous-hash field forms an optional append-only receipt chain. Tampering
with a count, root, status, partition key, or timestamp invalidates the receipt.

Receipt integrity proves that a specific declared stream was processed. It does
not by itself justify promotion to empirical or canonical status.

## 9. Transactional SQLite control plane

`FrontierStore` is intentionally a control plane rather than a payload lake.

It stores:

- virtual plan definitions;
- seeded partition pages;
- pending, leased, and completed status;
- worker leases and expiry;
- receipts;
- exact content fingerprints;
- frontier events.

It does not store billions of generated JSON payloads in one SQLite database.

Recommended storage split:

```text
Git
├── code
├── schemas
├── small manifests
├── selected receipts
└── reproducible tests

SQLite control plane
├── leases
├── partition state
├── receipt index
├── exact dedup
└── frontier events

Object / columnar storage
├── compressed JSONL
├── Parquet
├── SQLite domain partitions
├── checksums
└── cold generated payloads
```

## 10. Worker leases

Workers claim partitions through `BEGIN IMMEDIATE` transactions. A lease
contains:

- worker ID;
- partition key;
- opaque token;
- expiry;
- status transition.

Expired leases return to `pending` and can be reclaimed. Heartbeats extend an
active lease. Completion requires a valid receipt matching the exact plan,
partition, worker, and logical record count.

The independent `LeaseAuthority` can also issue stateless HMAC-SHA256 signed
leases for distributed dispatch layers. Persistent claim state must still be
managed transactionally to prevent duplicate work.

## 11. Exact deduplication

The control plane records exact content fingerprints with:

- namespace;
- kind;
- first partition;
- byte size;
- first-seen time.

The first insertion succeeds. Repeated exact fingerprints are rejected without
deleting provenance.

Exact deduplication does not imply semantic equivalence. Future approximate or
embedding-based deduplication must carry explicit thresholds, models, versions,
false-positive studies, and OAK review.

## 12. OAK promotion ladder

R0.5 formalizes four levels.

### Candidate

Requires:

- structural validation;
- deterministic reproduction;
- complete provenance.

### Validated synthetic

Also requires:

- negative controls;
- baseline comparison;
- quantified uncertainty.

### Empirical

Also requires:

- real data;
- safety review where relevant.

### Canon

Also requires:

- independent review.

A trillion generated candidates cannot bypass one missing requirement.

```bash
omega-generator-frontier oak \
  --level validated_synthetic \
  --structural-validation \
  --deterministic-reproduction \
  --provenance-complete \
  --negative-controls \
  --baseline-comparison \
  --uncertainty-quantified
```

## 13. CLI operations

Create a quadrillion-scale virtual plan:

```bash
omega-generator-frontier plan \
  --profile quadrillion \
  --output generated/frontier-r05/quadrillion-plan.json
```

Include a bounded partition page:

```bash
omega-generator-frontier plan \
  --profile trillion \
  --page-cursor 1000000 \
  --page-limit 64
```

Initialize the control plane:

```bash
omega-generator-frontier db-init \
  --db generated/frontier-r05/control.sqlite3
```

Seed only the next page:

```bash
omega-generator-frontier db-seed \
  --db generated/frontier-r05/control.sqlite3 \
  --profile trillion \
  --cursor 0 \
  --limit 256
```

Claim work:

```bash
omega-generator-frontier db-claim \
  --db generated/frontier-r05/control.sqlite3 \
  --plan-fingerprint PLAN_SHA256 \
  --worker-id worker-001
```

Audit stored receipts:

```bash
omega-generator-frontier db-status \
  --db generated/frontier-r05/control.sqlite3 \
  --plan-fingerprint PLAN_SHA256 \
  --audit
```

## 14. GitHub scaling doctrine

Do not translate one logical record into one Git file or one commit.

Preferred path:

```text
logical search surface
→ virtual plan
→ bounded partition page
→ adaptive wave
→ streamed shard
→ MMR root
→ one receipt
→ compressed external artifact
→ selected manifest in Git
```

GitHub remains the review, provenance, policy, code, schema, and selected-proof
surface. It should not become an unbounded object store.

## 15. Security and failure modes

R0.5 explicitly expects:

- worker crashes;
- duplicated dispatch;
- stale leases;
- disk saturation;
- API throttling;
- partial shard writes;
- mismatched receipts;
- invalid hashes;
- cost overruns;
- quality regressions;
- false confidence caused by large counts.

Controls include:

- atomic status transactions;
- lease expiry;
- receipt verification;
- exact deduplication;
- append-only events;
- bounded pages;
- multi-resource budgets;
- OAK promotion gates;
- M⁻ saturation recording;
- dry-run planning before payload creation.

## 16. OAK boundary

R0.5 establishes scalable control and integrity infrastructure.

It does not establish:

- a trillion scientific discoveries;
- a trillion useful generators;
- empirical validation;
- novelty or patentability;
- industrial manufacturability;
- medical safety;
- legal compliance;
- product-market fit;
- revenue.

Every consequential claim remains governed by domain evidence, units,
provenance, uncertainty, baselines, negative controls, falsification, security,
safety, and independent review.
