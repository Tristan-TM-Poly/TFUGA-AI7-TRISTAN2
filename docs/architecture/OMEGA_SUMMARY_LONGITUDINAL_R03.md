# Ω-SUMMARY-FRACTAL-T∞ R0.3 — Longitudinal Corpus Observatory

## Goal

Turn repository summaries into a time-indexed, evidence-bounded observatory of a growing multi-repository corpus.

```text
Git repositories
    ↓
RepositoryScanner
    ↓
SummaryHypergraph D0..D9
    ↓
Evidence / chronology / proof-debt projections
    ↓
Summary snapshot S(t)
    ├── Markdown + JSON
    ├── GraphML + JSONL
    ├── ΔSummary
    └── hash-chained history
             ↓
      longitudinal metrics
             ↓
   convergence / super-kernel candidates
```

## 1. Snapshot identity

A summary snapshot has a deterministic `cache_fingerprint` derived from file hashes, depth, audience and focus.

The persistent index stores normalized snapshots, not arbitrary prose. Repository and corpus snapshots are projected into a common entity model.

## 2. Hash chain

Each logical history entry is:

```text
entry_n = {
  ordinal,
  previous_hash,
  entry_hash,
  snapshot
}

entry_hash = SHA256(previous_hash || canonical(snapshot))
```

Properties:

- append-only semantics;
- duplicate fingerprint suppression;
- deterministic integrity verification;
- no network or database required;
- portable JSON artifact.

The file itself is replaced atomically by the caller when persisted; “append-only” describes the logical history contract, not filesystem append syscalls.

## 3. Structural crystallization

For each system:

```text
C_struct = mean(
  documented,
  implemented,
  tested,
  linked_ci,
  schema_backed
)
```

Each component is Boolean and evidence-bound to repository structure.

This intentionally does **not** include:

- scientific truth;
- novelty;
- benchmark superiority;
- external replication;
- safety certification;
- product-market fit;
- revenue;
- patentability.

Those dimensions require separate evidence channels.

## 4. Structural proof debt

`D_struct` counts observable missing crystallization components under conservative rules:

- no documentation;
- no implementation;
- implemented without focused tests;
- implemented without linked CI;
- implemented without machine-readable contract.

External validation is never included as “present” merely because repository structure is healthy.

## 5. Velocity

The longitudinal report computes:

```text
velocity = ΔC_struct / max(1, observed_runs - 1)
```

The denominator is **observed runs**, not wall-clock time. This avoids fabricating a scientific/productivity rate from Git timestamps, CI replay timestamps or irregular sampling.

## 6. Multi-evidence convergence

Pair candidates retain independent evidence channels:

- lexical Jaccard;
- direct dependency;
- shared dependencies;
- validation-profile overlap.

A `multi-evidence-superkernel-candidate` requires at least two channels by default. Clusters are connected components over qualifying pairs.

Invariant:

```text
status = review_required
automatic_merge = false
```

Clustering is an architectural routing signal only.

## 7. Graph exports

Repository bundles can be emitted as:

- `SUMMARY_GRAPH.jsonl`: streamable node/edge records;
- `SUMMARY_GRAPH.graphml`: standard directed graph projection;
- `SUMMARY_GRAPH_EXPORT.json`: fingerprint/cardinality manifest.

This enables downstream graph databases and visualizers without making a graph database a runtime dependency.

## 8. Zero-touch behavior

### Repository

`omega-summary all-depths` automatically creates at D9:

```text
SUMMARY_HISTORY.json
longitudinal/
graph/
```

Identical fingerprints are idempotent.

### Corpus

`omega-summary-corpus` automatically creates:

```text
CORPUS_SUMMARY.json
CORPUS_SUMMARY.md
CORPUS_INDEX.json
longitudinal/
repositories/
```

when repository views are enabled.

## 9. Query layer target

R0.3 makes the following future queries mechanically possible:

```text
Which systems gained tests since the previous snapshot?
Which systems have decreasing structural proof debt?
Which systems repeatedly depend on the same primitives?
Which candidate super-kernels have two or more independent structural signals?
Which systems disappeared or were renamed?
Which repositories are drifting apart in contracts or validation coverage?
```

R0.3 does not yet solve semantic rename identity or causal genealogy.

## 10. OAK boundary

The longitudinal layer observes repository state. It does not convert repository motion into scientific progress.

```text
ΔGit ≠ ΔTruth
C_struct ≠ scientific validity
cluster ≠ identity
first_seen(Git) ≠ invention date
large generated space ≠ discovery
```

These inequalities are architectural invariants, not documentation disclaimers added after the fact.
