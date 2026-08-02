# Ω-HYPERKNOWLEDGE-T∞ R0.3

Status: **coded MVP / OAK-safe structural evidence graph / not scientific certification**.

## Purpose

R0.2 maps repository theories, statuses, risks, priorities, and paths. R0.3 adds the next epistemic layer: atomic claims, typed evidence, counterexamples, temporal OAK transitions, contradiction candidates, coverage metrics, and an actionable P0-P6 queue.

```text
repository theory node
→ knowledge cell
→ atomic claims
→ evidence and counterevidence
→ temporal OAK history
→ audit and contradictions
→ prioritized action queue
```

## Knowledge-cell contract

A cell separates:

- subject and definition;
- claim atoms with scope, polarity, assumptions, and failure conditions;
- equations, code, tests, datasets, baselines, measurements, results, proofs, counterexamples, and M-minus records;
- chronological OAK transitions and their causes;
- risks, aliases, source paths, owner, disclosure state, and next actions.

The schema is available at:

```text
schemas/knowledge-cell.schema.json
```

## Implemented modules

```text
omega_wiki_t/knowledge_cell.py
omega_wiki_t/contradiction_engine.py
omega_wiki_t/action_queue.py
omega_wiki_t/hyperknowledge.py
```

### `knowledge_cell.py`

Provides deterministic identifiers, claim/evidence/transition records, structural validation, coverage metrics, and audits for:

- unsupported claims;
- missing falsification conditions;
- physics claims without equations;
- promoted physics claims without measurements;
- results without baselines;
- code without tests;
- canonical status without decisive evidence;
- missing next actions;
- public disclosure with patent, confidentiality, or trade-secret risk.

### `contradiction_engine.py`

Groups claims by canonical proposition and distinguishes:

- potential contradiction: opposing polarity with overlapping scope;
- scope tension: opposing polarity with different or unclear scopes;
- probable duplicate: equivalent normalized claim text and polarity.

These are review candidates. The engine does not perform automated logical proof or semantic entailment certification.

### `action_queue.py`

Compiles findings into:

```text
P0 — blocking integrity, evidence, physics, IP, or contradiction risks
P1 — implementation close to usable but missing tests or equivalent gate
P2 — incomplete cells and claims
P3 — independent external enrichment
P4 — fertile backlog reserved for later expansion
P5 — contradiction, alias, duplicate, or quarantine review
P6 — archive and historical preservation
```

### `hyperknowledge.py`

Emits:

```text
manifest.json
knowledge-cells.json
knowledge-cells.jsonl
audit.json
claim-collisions.json
action-queue.json
action-queue.jsonl
report.md
```

## Initial complete cells

### FFWT-HAC-CVCD

The cell preserves the important negative result:

- exact Haar reconstruction worked;
- naive fractal weighting did not outperform Haar on the recorded synthetic reconstruction task;
- the overly broad superiority interpretation was refuted locally;
- the branch was reformulated toward anomaly detection, denoising, and classification with stronger baselines.

The transition history is explicit:

```text
IDEA → FORMALIZED → SIMULATED → REFUTED → REFORMULATED
```

This prevents a failed local benchmark from disappearing while also preventing it from being inflated into a universal refutation.

### Ω-LIN-T

The second cell validates schema reuse on local linearization:

```text
IDEA → FORMALIZED → IMPLEMENTED → DEMONSTRATED
```

It binds the claim to a local equation, code, tests, baselines, residual report, validity-domain limits, and next experiments. Demonstrated does not mean universal theorem.

## CLI

```bash
omega-wiki build-cells \
  data/knowledge_cells/ffwt_hac_cvcd_r0_3.json \
  data/knowledge_cells/omega_lin_t_r0_3.json \
  --output-dir generated/omega_wiki_t/hyperknowledge-r0-3
```

Or:

```bash
python examples/omega_hyperknowledge_r0_3_demo.py
```

## Metrics

R0.3 calculates:

```text
evidence_coverage
falsification_coverage
traceability_coverage
cell_count
claim_count
finding_count
```

Future releases should add:

```text
baseline_coverage
measurement_coverage
negative_memory_propagation
alias_resolution_rate
stale_status_ratio
independent_replication_coverage
canonical_density
```

## OAK promotion boundary

R0.3 does not automatically authorize status promotion. In particular:

- a concept is not a claim;
- a claim is not proof;
- a citation is not automatic support;
- code is not validation;
- a result is limited to its protocol and scope;
- a generated contradiction is a review candidate;
- a complete schema record is not scientific certification;
- public disclosure, patent filing, safety decisions, and external publication remain human-approved actions.

## Next gates

1. Add exact source locators and content hashes to all evidence records.
2. Connect cells to the R0.2 theory hypergraph through stable system IDs.
3. Add independent external enrichment from Wikidata, DOI, arXiv, ISBN, standards, and prior-art sources.
4. Add unit-aware equation records and calibrated measurement records.
5. Add semantic alias decisions: exact, probable, historical, overlap, specialization, and not-equivalent.
6. Add incremental cell regeneration from repository changes.
7. Add interactive queries for unsupported claims, missing baselines, stale status, contradictions, IP risk, and highest-information-gain tests.
