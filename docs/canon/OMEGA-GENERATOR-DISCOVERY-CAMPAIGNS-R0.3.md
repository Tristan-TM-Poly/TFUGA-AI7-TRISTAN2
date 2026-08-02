# Ω-GENERATOR-DISCOVERY-CAMPAIGNS R0.3

## Million-record streaming campaigns without a permanent addition ceiling

**Status:** executable research infrastructure. Generated records are candidate templates and synthetic benchmark specifications, not discoveries, proofs, empirical validations, patentability conclusions, or revenue evidence.

## Default campaign

R0.3 expands the default search surface to:

```text
32 domains
× 32 operator families
× 8 scales
× 4 representations
× 4 evidence modes
= 131,072 generator candidates
```

Each generator receives eight linked synthetic benchmark templates:

```text
131,072 × 8 = 1,048,576 synthetic benchmarks
```

Total logical additions:

```text
131,072 + 1,048,576 = 1,179,648 records
```

This is a finite default campaign, not a permanent maximum. A campaign specification can add axes, values, benchmark variants, partitions, and later evidence layers. Every concrete execution remains bounded by actual compute, storage, validation, GitHub rules, cost, safety, IP classification, and rollback capacity.

## Why 1,024 is no longer the architecture

A shard may still contain 1,024 or 2,048 generator bundles because transaction size and total campaign size are different concepts:

```text
runtime shard granularity != total logical additions != scientific evidence density
```

The implementation contains no `MAX_ADDITIONS = 1200`. It uses:

- mixed-radix indexing instead of a materialized Cartesian product;
- lazy generator and benchmark streams;
- balanced partitions without overlap;
- deterministic identifiers and campaign fingerprints;
- atomic JSONL shard replacement;
- checkpointed resume after every completed shard;
- generator-bundle locality so linked benchmarks never drift to another partition;
- planner-ready records compatible with `omega-unbounded plan`;
- OAK boundaries carried in manifests and records.

## Commands

Plan the full default campaign across 64 balanced partitions:

```bash
omega-generator-campaign plan --partition-count 64 --include-partitions
```

Stream and hash 16,384 bundles, representing 147,456 logical records, without writing the entire campaign:

```bash
omega-generator-campaign stress --generator-bundles 16384
```

Emit one resumable partition:

```bash
omega-generator-campaign emit \
  --partition-count 64 \
  --partition-index 0 \
  --bundles-per-shard 2048 \
  --output-dir generated/omega_generator_campaign_r03/p000
```

Resume safely after interruption:

```bash
omega-generator-campaign emit \
  --partition-count 64 \
  --partition-index 0 \
  --bundles-per-shard 2048 \
  --output-dir generated/omega_generator_campaign_r03/p000 \
  --resume
```

Compile an emitted JSONL shard into a reversible GitHub tree plan:

```bash
omega-unbounded plan \
  generated/omega_generator_campaign_r03/p000/records/bundle-000000000-000002048.jsonl \
  --output-dir generated/github-plan-p000-s000
```

## Configurable axes

A JSON specification may replace or extend the default axes:

```json
{
  "campaign_id": "omega-generator-custom-r03",
  "benchmark_variants": 12,
  "axes": {
    "domains": ["spectral", "crystal"],
    "families": ["translation", "dilation", "rotation"],
    "scales": ["micro", "meso", "macro"],
    "representations": ["state", "operator", "hypergraph"],
    "evidence_modes": ["reconstruction", "prediction", "intervention"]
  }
}
```

The implementation validates empty and duplicate axis values, computes exact cardinality before generation, and fingerprints the complete campaign definition.

## GitHub scaling rule

Millions of logical additions should not become millions of GitHub files or commits. The production path is:

```text
logical records
→ linked generator bundles
→ streamed JSONL shards
→ semantic/deduplicated tree plans
→ bounded atomic commits
→ one reviewable pull request
```

Large cold artifacts should move to Releases, Git LFS, object storage, Parquet, SQLite, or a graph database while Git retains manifests, hashes, schemas, selected hot shards, tests, and provenance.

## OAK promotion ladder

A generated candidate stays a candidate until it gains, where relevant:

1. typed inputs, outputs, and units;
2. explicit governing assumptions and domain of validity;
3. baseline comparison;
4. uncertainty and identifiability analysis;
5. negative controls and counter-hypotheses;
6. out-of-sample reconstruction or prediction;
7. falsification attempts;
8. reproducible implementation;
9. real data provenance;
10. independent review for consequential claims.

The million-record campaign increases navigable optionality. It does not multiply truth by enumeration.
