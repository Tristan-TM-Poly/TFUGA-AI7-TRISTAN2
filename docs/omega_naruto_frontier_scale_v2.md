# Ω-NARUTO Frontier Scale v2

## Status

Frontier Scale v2 is an executable corpus-generation and integrity-testing system.
Naruto-inspired terms remain engineering metaphors. Generated records are test
fixtures, not evidence that fictional mechanisms exist and not scientific
validation of a theory.

## Why this exists

Counting repository source lines is a weak measure of productive scale. A useful
large iteration should create many independently addressable, reproducible and
verifiable objects without forcing Git to store millions of nearly repetitive
lines forever.

Frontier Scale v2 therefore separates:

1. the compact generator and validator committed to Git;
2. the generated corpus stored as sharded compressed artifacts;
3. the manifest, hashes, index and M⁻ telemetry that prove what was produced;
4. the finite resource budget of one run;
5. the architecture's absence of a permanent total-record ceiling.

## Deterministic global address space

The seed axes define 64,512 local combinations per epoch:

- 12 operators;
- 8 domains;
- 7 epistemic states;
- 4 evidence modes;
- 6 perturbations;
- 4 gate profiles.

A global ordinal is decomposed into:

```text
epoch = ordinal // 64,512
local_ordinal = ordinal % 64,512
```

The epoch is included in the canonical record identity. Consequently, ordinal
64,512 is not truncated or aliased with ordinal 0. The system continues into
new deterministic epochs for 100k, 1M, 10M or larger finite experiments.

## Scale plan

`plan_scale_run` partitions a requested finite range into contiguous shards.
For the default million-record proof:

```text
start ordinal:       0
target records:      1,000,000
records per shard:   25,000
shards:              40
workers:             2
completed epochs:    15
partial epoch:       32,320 records
```

No constant such as `MAX_RECORDS = 1_000_000` exists. One million is the current
verified experiment, not the architectural maximum.

## Independent compressed shards

Each partition produces:

```text
scale-<first>-<last>.jsonl.gz
scale-<first>-<last>.receipt.json
```

The receipt records:

- global ordinal range;
- record count;
- compressed and uncompressed byte counts;
- SHA-256 of the compressed bytes;
- SHA-256 of the logical uncompressed JSONL stream;
- compression codec;
- deterministic partition identity.

Gzip timestamps are fixed to zero. Equivalent sequential and parallel runs must
therefore produce identical compressed hashes, logical hashes and Merkle roots.

## Atomicity and resume

Data and receipt files are written through temporary files and atomically
renamed. A resumed run verifies every existing receipt and shard before reuse.
A shard is regenerated when any of the following changes:

- requested ordinal range;
- record count;
- file name;
- compressed byte count;
- compressed SHA-256;
- gzip decodability;
- uncompressed byte count;
- logical SHA-256.

A successful second pass over the same million-record configuration must report:

```text
resumed_shards = 40
generated_shards = 0
```

## Parallel generation

Partitions are independent. `ProcessPoolExecutor` distributes missing shards
across local workers. Output order is restored by partition ID before manifest
construction. The number of workers may change performance, but must never
change corpus content.

The unit suite compares one-worker and two-worker runs and requires identical:

- logical corpus SHA-256;
- Merkle root;
- compressed byte total;
- per-shard compressed hashes;
- per-shard logical hashes.

## Streaming validation

`validate_scale_corpus` validates records without storing one million IDs in a
set. For each expected global ordinal, it recomputes the canonical record and
checks:

- ordinal continuity;
- deterministic record ID;
- epoch and local ordinal;
- operator and domain;
- epistemic state and evidence mode;
- perturbation and gate profile;
- expected OAK action;
- compressed and logical shard hashes;
- corpus logical hash;
- Merkle root;
- record and byte totals.

This replaces an O(N)-memory uniqueness table with deterministic O(1)-record
memory validation. Memory still depends on decompression buffers and Python
runtime overhead, but not on retaining every record object.

## Streaming index

`build_scale_index` creates exact aggregates for:

- epochs;
- operators;
- domains;
- epistemic states;
- evidence modes;
- perturbations;
- gate profiles;
- expected OAK actions;
- M⁻ routing;
- blocking;
- human review;
- local ranking;
- local-combination coverage.

Only a bounded sample is retained. Local coverage uses a byte array of 64,512
positions rather than a million-record object graph.

## Exact one-million routing distribution

For the default axes and the range `[0, 1,000,000)`, the expected routing is:

| OAK action | Records |
|---|---:|
| `BLOCK_AND_RETAIN_MMINUS` | 500,000 |
| `REJECT_UNSUPPORTED_AND_RETAIN_MMINUS` | 125,004 |
| `WARN_REQUIRE_HUMAN_REVIEW` | 187,498 |
| `RANK_LOCALLY_WITHOUT_CERTIFICATION` | 156,249 |
| `RECOMPUTE_GATES_BEFORE_SELECTION` | 31,249 |
| **Total** | **1,000,000** |

Derived totals:

```text
M⁻ records:                 625,004
blocked records:            500,000
human-review records:       187,498
locally ranked records:     156,249
covered local combinations: 64,512 / 64,512
repeated axis realizations: 935,488
```

These are deterministic fixture-routing counts. They are not measurements of
real-world risk prevalence.

## Commands

### Plan

```bash
python -m omega_naruto_hmagfm.scale_cli plan \
  --target 1000000 \
  --shard-records 25000
```

### Generate

```bash
python -m omega_naruto_hmagfm.scale_cli generate \
  --output-dir generated/omega_naruto/scale-1m \
  --target 1000000 \
  --shard-records 25000 \
  --workers 2 \
  --compression-level 6
```

### Validate

```bash
python -m omega_naruto_hmagfm.scale_cli validate \
  --output-dir generated/omega_naruto/scale-1m \
  --report generated/omega_naruto/scale-validation.json
```

### Index

```bash
python -m omega_naruto_hmagfm.scale_cli index \
  --output-dir generated/omega_naruto/scale-1m \
  --destination generated/omega_naruto/scale-index.json \
  --sample-limit 128
```

## Continuing past one million

A later run may start exactly at the previous `next_ordinal`:

```bash
python -m omega_naruto_hmagfm.scale_cli generate \
  --output-dir generated/omega_naruto/scale-1m-to-2m \
  --start-ordinal 1000000 \
  --target 1000000 \
  --shard-records 25000 \
  --workers 2
```

Separate output directories preserve immutable run configurations. A higher
layer may later join manifests into a multi-run ledger.

## Resource limits versus permanent limits

Every physical execution remains constrained by:

- GitHub Actions runtime;
- available cores and memory;
- temporary disk;
- artifact size and retention;
- compression cost;
- validation time;
- repository and API quotas;
- useful semantic diversity;
- review capacity.

Those constraints are not hidden. Saturation must produce an M⁻ incident such
as:

```text
observed limit
→ exact run configuration
→ last valid ordinal and shard
→ resource measurement
→ failed invariant
→ recovery or rollback
→ architecture change
→ larger next experiment
```

## M⁻ saturation protocol

A scale experiment is not successful merely because the process exits zero.
The following failures must be retained:

- duplicate or missing ordinal;
- nondeterministic shard hash;
- worker-count-dependent output;
- invalid gzip stream;
- receipt mismatch;
- logical corpus hash mismatch;
- Merkle mismatch;
- resume regeneration of valid shards;
- memory growth proportional to total record IDs;
- unacceptable artifact or runtime cost;
- combinatorial expansion with no additional useful coverage.

The last item is essential: more generated objects are valuable only when they
increase test coverage, discrimination, falsification, reusable data or product
capability.

## CI proof

`.github/workflows/omega-naruto-frontier-scale.yml` performs the current scale
proof on Python 3.11:

1. compile the scale engine;
2. run scale tests;
3. plan 1M records;
4. generate 40 compressed shards with two workers;
5. rerun generation and require zero regenerated shards;
6. stream-validate all one million records;
7. build the aggregate index and M⁻ telemetry;
8. validate manifest, validation and index JSON Schemas;
9. assert the exact million-record routing distribution;
10. upload the complete compressed proof artifact.

The workflow accepts manual finite targets. A future 10M run is therefore a
resource experiment, not a source-code change to remove a hard maximum.

## Next architecture

Priority extensions after the 1M proof:

- multi-run ledger and manifest federation;
- deterministic remote worker partition leasing;
- object-storage backends;
- zstd and columnar Parquet projections;
- Bloom filters and disk-backed exact deduplication for noncanonical inputs;
- semantic novelty and equivalence clustering;
- mutation-based adversarial corpus generation;
- benchmark outcome ingestion;
- M⁻ saturation dashboard;
- adaptive allocation toward high-information regions;
- 10M and 100M experiments only after throughput, cost and semantic-value review.

## OAK boundary

One million valid records prove that the software produced and verified one
million deterministic fixtures under the tested configuration. They do not
prove one million discoveries, one million useful ideas, a physical theory, a
commercial product, institutional validation or universal superiority.
