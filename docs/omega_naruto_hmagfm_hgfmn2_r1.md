# Ω-NARUTO-HMAGFM-HGFMnD² — R1.2 Frontier 100k

**Status:** exploratory architecture + executable OAK software scaffold + unbounded-by-design corpus frontier.  
**Boundary:** Naruto and Naruto Shippuden provide design metaphors. No fictional mechanism is asserted to exist physically.

## Purpose

R1.2 converts narrative operators into bounded engineering objects:

- chakra → compute, memory, energy, time, attention, and human-review budgets;
- Kage Bunshin → isolated parallel proposals with evidence and provenance;
- Byakugan → observability through deterministic graph export;
- Genjutsu → adversarial checks for fabricated, circular, private, or inflated claims;
- seals → PrivacyGate, IPGate, SafetyGate, maturity, evidence, and human-review requirements;
- M⁻ → retained rejected conclusions and their failure reasons;
- Ω-SANS-PLAFOND → streaming epochs, adaptive targets, sharding, checkpointing, hashes, resume, and backpressure.

## Core pipeline

```text
hypothesis
→ bounded clone proposals
→ evidence/provenance/risk checks
→ OAKMerge ranking
→ contradictions + M⁻
→ publication gates
→ HGFMnD² JSON/GraphML
→ robustness scenarios
→ unbounded global ordinals
→ sharded corpus
→ streaming validation
→ reviewable artifacts
```

Selection is not certification. A high local score or large corpus is not proof, institutional approval, or authorization to publish.

## Epistemic ladder

```text
F0 fiction/metaphor
I1 intuition
H2 falsifiable hypothesis
D3 formal definition
S4 simulation
P5 prototype
B6 reproducible benchmark
E7 experimental evidence
R8 independent replication
C9 domain-bounded canon
```

## OAKMerge

`oak_merge` rejects or retains proposals when they:

- exceed the available `ChakraBudget`;
- cross privacy, IP, or safety thresholds;
- lack evidence or provenance.

Supported candidates are ranked deterministically. Contradictions are preserved instead of erased, and rejected proposals remain available as falsification memory.

## Genjutsu audit

The deterministic red-team layer flags:

- fabricated or placeholder source markers;
- circular evidence;
- private or restricted source markers;
- benchmark-or-higher status with insufficient artifacts;
- missing provenance;
- confidence/uncertainty mismatch.

These rules are adversarial lint, not a universal deception detector.

## Baseline benchmark

The included fixture compares evidence-aware OAKMerge with majority vote and highest self-reported confidence. Two unsupported clones agree while one documented minority clone disagrees. OAKMerge selects the documented result in this fixture only.

## HGFMnD² export

`build_hgfmn_graph` emits deterministic JSON and GraphML nodes/edges for hypotheses, proposals, evidence, provenance, local selection, contradictions, and M⁻ retention. Graph presence does not validate a node's truth.

## Robustness analysis

R1.2 perturbs confidence, uncertainty, evidence, rivals, and risk. The default fixture intentionally exposes one instability: once the selected proposal crosses the risk gate, no proposal remains acceptable.

## Frontier 100k

The seed projection contains 64,512 combinations per epoch. Global ordinals continue beyond that projection:

```text
epoch = ordinal // 64,512
local_ordinal = ordinal % 64,512
```

The CI generates and validates 100,000 records, crossing into epoch 1. The system does not truncate targets at 64,512.

Each record contains:

- global ordinal;
- epoch and local ordinal;
- deterministic record ID;
- operator;
- domain;
- epistemic state;
- evidence mode;
- perturbation;
- gate profile;
- expected OAK action;
- explicit non-claim boundary.

The 100k corpus is split into ten 10,000-record JSONL shards. Every shard and the global corpus are SHA-256 verified.

## Run

```bash
python -m pytest -q tests/test_omega_naruto*.py

python -m omega_naruto_hmagfm.cli \
  --output generated/omega_naruto/report.json \
  --graphml-output generated/omega_naruto/graph.graphml

python -m omega_naruto_hmagfm.corpus_cli generate \
  --output-dir generated/omega_naruto/frontier-100k \
  --target 100000 \
  --shard-records 10000

python -m omega_naruto_hmagfm.corpus_cli validate \
  --output-dir generated/omega_naruto/frontier-100k
```

`--target` bounds one execution; it is not a permanent architecture maximum.

## Verified CI surface

The dedicated workflow runs on Python 3.10, 3.11, and 3.12. It:

- compiles the package and tests;
- runs the focused core/frontier test suite;
- parses six JSON Schemas;
- validates the core report and graph;
- proves deterministic epoch crossing;
- tests resume and global hash preservation;
- generates 100,000 records on Python 3.11;
- validates 100,000 unique IDs and continuous ordinals;
- uploads the complete compressed corpus and reports.

## Non-claims

This module does not claim chakra or jutsu as physical mechanisms, free energy, zero dissipation, autonomous scientific certification, universal superiority, permission to expose private/IP-sensitive information, or replacement of experts and human judgment.

Corpus cardinality measures generated test capacity, not scientific truth, useful coverage, product value, or market proof.

## Next scale gates

- 250k and 1M frontier experiments;
- compression and columnar indexes;
- parallel deterministic shard workers;
- semantic deduplication;
- M⁻ saturation telemetry;
- adaptive validation sampling plus full hash checks;
- distributed epochs;
- coverage-quality benchmarks rather than raw quantity alone.
