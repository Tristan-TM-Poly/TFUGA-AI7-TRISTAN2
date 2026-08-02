# Ω-GENERATOR-DISCOVERY R0.3 Ultra — Partitioned Index

## Final GitHub-compatible storage architecture

The R0.3 Ultra atlas contains 393,216 linked JSONL records:

- 65,536 generator candidates;
- 131,072 synthetic benchmark specifications;
- 65,536 ordered-composition hyperedges;
- 65,536 mandatory negative controls;
- 65,536 validation-ledger entries.

A first validated build produced one SQLite database of 241.89 MB. The database passed generation, deterministic regeneration, cross-link validation and the full ten-test OAKBench, but GitHub rejected the push because a single file exceeded the 100 MB per-file limit.

The final architecture preserves every record and replaces the monolith with:

```text
generated/omega_generator_discovery_r03_ultra/index/
├── routing.sqlite3
├── partition-report.json
└── domains/
    ├── spectral.sqlite3
    ├── crystal.sqlite3
    ├── elastic.sqlite3
    ├── ...
    └── game.sqlite3
```

There are 32 domain databases plus one compact routing database. Every database is verified below GitHub's per-file limit before publication.

## Query routing

Global filters use `routing.sqlite3`:

- generator ID;
- ordinal;
- domain;
- family;
- scale;
- representation;
- regime;
- status;
- invariant;
- risk tier;
- inverse support.

After the router identifies a generator's domain, the API opens only the corresponding domain partition to retrieve:

- the full generator payload;
- its two benchmarks;
- its ordered-composition hyperedges;
- its negative control;
- its validation decision.

This preserves a simple public API while avoiding a monolithic database.

## Validation sequence

The GitHub workflow performs the following sequence:

1. generate the 393,216 JSONL records;
2. create a temporary monolithic SQLite index for exhaustive validation;
3. validate exact counts and all cross-links;
4. regenerate and compare the combined SHA-256 fingerprint;
5. partition the index into 32 domains plus a router;
6. verify aggregate counts across every partition;
7. verify exhaustive treatment of high-risk candidates;
8. verify that every committed SQLite file is below 100 MB;
9. run the R0.3 Ultra OAKBench against the partitioned API;
10. delete the temporary monolithic index;
11. commit only the validated partitioned atlas.

## M⁻ memory

```text
M⁻-R03-INDEX-001
Failure: monolithic SQLite index exceeded GitHub's 100 MB per-file limit.
Observed size: 241.89 MB.
What remained valid: all 393,216 records, deterministic fingerprint, links and tests.
Correction: partition by domain and add a routing database.
Anti-error rule: estimate and gate individual artifact size before remote publication.
Generalization: sharding must apply not only to JSONL data but also to derived indexes.
```

The correction increases architectural quality rather than reducing the scientific frontier.

## OAK boundary

Partitioning improves storage and retrieval. It does not increase the truth status of any candidate. Generated records remain research infrastructure until they receive units, provenance, uncertainty, baselines, real data, negative controls, falsification and domain review.
