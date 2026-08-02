# Ω-NARUTO-HMAGFM Frontier — 100k+ corpus architecture

**Status:** executable, deterministic, OAK-bounded corpus-generation infrastructure.

## Why this exists

A few thousand handwritten lines do not satisfy Ω-SANS-PLAFOND-T. The objective is not to inflate the repository with repetitive text. The objective is to create a system that can produce, validate, shard, checkpoint, resume, hash, compare, and archive tens of thousands to millions of meaningful test records per iteration.

The permanent rule is:

```text
no arbitrary total-record ceiling
+ finite resource-bounded executions
+ backpressure
+ checkpoints
+ deterministic IDs
+ shard hashes
+ global hash
+ validation
+ M⁻ saturation memory
```

## Initial projection

The seed axis product contains:

```text
12 operators
× 8 domains
× 7 epistemic states
× 4 evidence modes
× 6 perturbations
× 4 gate profiles
= 64,512 combinations per epoch
```

This is not a maximum. Global ordinals continue into deterministic epochs:

```text
epoch = ordinal // 64,512
local_ordinal = ordinal % 64,512
```

Epoch is included in the record identity, so the same local combination in a later epoch remains distinct and reproducible.

## Current CI proof

The dedicated GitHub Actions workflow generates and validates **100,000 records** on Python 3.11. This deliberately crosses the first 64,512-record epoch.

Expected outputs:

```text
generated/omega_naruto/frontier-100k/
├── corpus-000000.jsonl
├── corpus-000001.jsonl
├── ...
├── corpus-000009.jsonl
├── checkpoint.json
└── manifest.json

generated/omega_naruto/
├── frontier-axes.json
├── frontier-generation.json
├── frontier-validation.json
└── frontier-validation-stdout.json
```

Each of the ten shards contains 10,000 records.

## Integrity invariants

The validator checks:

- every declared shard exists;
- each shard SHA-256 matches;
- each shard byte count matches;
- each shard record count matches;
- ordinals are continuous;
- record IDs are non-empty and unique;
- every record preserves the OAK non-claim boundary;
- the observed total matches the manifest;
- the global corpus SHA-256 matches;
- no P0 finding remains.

## Commands

Inspect the seed axes:

```bash
python -m omega_naruto_hmagfm.corpus_cli inspect --pretty
```

Generate 100,000 records:

```bash
python -m omega_naruto_hmagfm.corpus_cli generate \
  --output-dir generated/omega_naruto/frontier-100k \
  --target 100000 \
  --shard-records 10000
```

Validate the corpus:

```bash
python -m omega_naruto_hmagfm.corpus_cli validate \
  --output-dir generated/omega_naruto/frontier-100k \
  --report generated/omega_naruto/frontier-validation.json
```

Generate one million records for a finite experiment:

```bash
python -m omega_naruto_hmagfm.corpus_cli generate \
  --output-dir generated/omega_naruto/frontier-1m \
  --target 1000000 \
  --shard-records 25000
```

`--target` bounds one execution. It is not a permanent system maximum.

## Adaptive growth

Without an explicit target, the API can derive the next run from:

- the previous successful record count;
- a multiplicative growth factor;
- estimated bytes per record;
- available storage budget;
- a minimum useful experiment size.

Example progression:

```text
25,000 → 50,000 → 100,000 → 200,000 → 400,000 → ...
```

Resource pressure can reduce a particular run through backpressure, but it does not create a permanent cap. The next architecture iteration may change sharding, compression, storage, parallelism, validation sampling, or distribution.

## OAK boundary

Large corpus cardinality is not evidence of scientific truth, usefulness, market value, or universal coverage. Scale becomes valuable only when records are discriminating, traceable, reproducible, and connected to real tests.

The frontier therefore separates:

```text
capacity
≠ coverage
≠ correctness
≠ evidence
≠ validation
≠ product value
```

## Next scale gates

1. 250k and 1M CI or scheduled frontier experiments.
2. Compressed JSONL/Zstandard shards.
3. Parallel shard generation with deterministic merge order.
4. SQLite or Parquet indexes for selective retrieval.
5. Property-based mutation of evidence and gate profiles.
6. Cross-corpus semantic deduplication.
7. M⁻ saturation ledger for storage, runtime, memory, API, and artifact limits.
8. Adaptive validation sampling plus full hash verification.
9. Distributed epochs across independent workers.
10. Benchmarking useful coverage rather than raw quantity.
