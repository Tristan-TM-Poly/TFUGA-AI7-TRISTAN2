# TFUGA / SAGE-TRISTAN

**Status:** v0.5 publication scaffold, derived from *Univers mathematique TFUGA / SAGE-TRISTAN v0.1 + Omega3-Omega6*.

This repository crystallizes a rigorous, testable, reusable layer of the TFUGA / SAGE-TRISTAN mathematical biosphere.

The central thesis is:

> A fertile structure is a generative compression that remains stable under transformations.

The operational pipeline is:

```text
raw intuition -> formal object -> equation -> proof -> algorithm -> simulation -> prototype -> minimal fertile canon
```

## Core objects

- `DCT++`: minimal research packet: Document, Code, Test, Data, Risk, Ethics, Status, Next, Links.
- `HGFM`: hypergraphe fractal mycelien for transversal couplings between theories, proofs, tests, artifacts, risks, and applications.
- `PowerScore`: log-stable maturity score balancing fertility, verifiability, reusability, impact, compression, and stability against complexity, noise, untested speculation, risk, and duplication.
- `Omega6`: parallel HGFM64 architecture: 64 coupled crystals across 8 master hyperedges.
- `AI-7`: metabolism of production, verification, testing, analysis, optimization, reproduction, integration, crystallization, stabilization, documentation, and promotion.
- `Ω-DeepTech Intelligence Forge`: OAK-safe layer for deeptech signals -> IP triage -> prototype tasks -> revenue routing -> GitHub artifacts.
- `Ω-ECC-T`: OAK-safe error-correction lab: Hamming(7,4), channel models, Syndrome-CVCD, HyperParityGraph-T, M⁻ hooks, and deterministic OAKBench.
- `Ω-PDF-HYPERGRAPH-GITHUB-T`: OAK-safe universal absorber for PDF/ZIP/text/code corpora -> chunks -> claim candidates -> HGFM/CVCD hypergraph -> GitHub-ready artifacts.
- `Ω-WIKI-T∞ / WikiForge-T`: multilingual Wikipedia reader and repository-theory absorber -> revision-pinned articles or canon files -> traceable claims/nodes -> citations, risks, next actions, and knowledge hypergraphs.
- `Ω-HYPERKNOWLEDGE-T∞ R0.3`: atomic claims -> typed evidence and counterevidence -> temporal OAK transitions -> contradiction candidates -> coverage metrics -> P0-P6 action queue.
- `Ω-QUATERNION-CRYSTAL-T`: tested 3D kernel separating quaternion orientation, affine deformation, stress/strain tensors, cubic elasticity, and Schmid projection.
- `Ω-LOGEXP-MORPH-T∞²`: guarded generator calculus with matrix exp/log, nilpotent lifting, BCH, active singular sectors, polar-log, Magnus, commutator graphs, MorphCodex, and basis compression.

## Repository structure

```text
docs/          Manifest, roadmap, canon analysis, publication plan.
schemas/       JSON schemas for DCT++, research cards, HGFM, WikiForge claims, and R0.3 knowledge cells.
data/knowledge_cells/ Checked-in FFWT-HAC-CVCD and Ω-LIN-T evidence cells.
sage_tristan/  Minimal Python engine for scoring, cards, status, HGFM, claims, AI-7 traces.
omega_deeptech_forge/ Minimal OAK-safe deeptech/IP/revenue triage engine.
ecc_tristan/   Minimal Ω-ECC-T executable lab for error correction, OAK, and M⁻.
omega_prof_poly_t/ Omega absorb systems, including the universal corpus absorber.
omega_wiki_t/  Wikipedia evidence compiler, theory hypergraph builder, knowledge-cell audit, contradiction engine, and action queue.
omega_quaternion_crystal_t/ Quaternion, affine, crystal, stress, and elasticity operators.
omega_logexp_morph_t/ Logarithmic/exponential morphism, active-factorization, and generator-compression kernel.
generated/omega_wiki_t/ Reproducible WikiForge evidence and hyperknowledge artifacts.
tests/         Unit tests for the executable core.
examples/      Example branches and DCT++ packets.
reports/       Generated audit and publication reports.
```

## Scientific hygiene

Names are not proofs. A named object becomes publishable only when it has a definition, hypotheses, test, limits, status, and promotion path. Strong claims are recoded into testable models before promotion.

```text
Name makes callable. Formalization makes testable. Testing makes credible. Proof makes canonizable. Reuse makes fundamental.
```

## Quick start

```bash
python -m pytest
python -m sage_tristan.demo
python examples/omega_deeptech_forge_demo.py
python examples/omega_ecc_t_demo.py
python examples/omega_universal_absorber_demo.py
python examples/omega_wiki_t_demo.py
python examples/omega_hyperknowledge_r0_3_demo.py
python examples/omega_quaternion_crystal_demo.py
python examples/omega_logexp_morph_demo.py
python examples/omega_logexp_morph_r0_3_demo.py
omega-quaternion-crystal --axis 0 0 1 --angle-deg 90 --vector 1 0 0
omega-logexp-morph --generator '[[0,0.1],[-0.1,0]]'
```

Universal corpus absorption dry-run:

```bash
omega-corpus-absorb path/to/corpus_or_zip --output-dir generated/omega_corpus
```

Multilingual Wikipedia evidence bundle:

```bash
omega-wiki read "Mécanique quantique" --lang fr
omega-wiki languages "Mécanique quantique" --lang fr
omega-wiki compile "Mécanique quantique" --lang fr --langs en,de,ja --output-dir generated/q944
omega-wiki audit generated/q944
```

Repository theory absorption and useful knowledge hypergraph:

```bash
omega-wiki absorb-theory \
  --canon-json interfaces/chatgpt-tristan-v2/data/theory-canon.json \
  --master-canon docs/00_MASTER_CANON_TFUGA_AI7_AIT.md \
  --system-index MASTER_SYSTEM_INDEX.md \
  --output-dir generated/omega_wiki_t/theory-canon-r0-2
```

R0.3 atomic knowledge cells, evidence audit, contradictions, metrics, and action queue:

```bash
omega-wiki build-cells \
  data/knowledge_cells/ffwt_hac_cvcd_r0_3.json \
  data/knowledge_cells/omega_lin_t_r0_3.json \
  --output-dir generated/omega_wiki_t/hyperknowledge-r0-3
```

The R0.2 canon absorption emits 92 nodes and 94 hyperedges. R0.3 does not replace it: R0.2 maps systems and routes, while R0.3 decomposes selected nuclei into claims, evidence, tests, results, counterexamples, temporal transitions, and actionable residues.

WikiForge-T remains extraction and knowledge-organization infrastructure, not factual certification. Wikipedia text is not proof; a citation marker is not automatically support; repository canon is not automatically scientific validation; code and passing structure checks do not certify a scientific claim.

## Output families

Universal absorber:

```text
manifest.json
chunks.jsonl
claims.jsonl
hypergraph.json
hypergraph.graphml
oak_report.json
```

WikiForge-T Wikipedia:

```text
manifest.json
articles.jsonl
claims.jsonl
sources.jsonl
language-matrix.json
report.md
```

WikiForge-T theory hypergraph R0.2:

```text
manifest.json
knowledge-hypergraph.json
knowledge-hypergraph.graphml
theory-nodes.jsonl
knowledge-hyperedges.jsonl
useful-knowledge.md
```

Ω-HYPERKNOWLEDGE-T∞ R0.3:

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

A compact R0.2 core projection is available at:

```text
generated/omega_wiki_t/theory-canon-r0-2/knowledge-hypergraph-core.json
```

## Current canon layer

Immediate canonizable modules:

- PowerScore
- DCT++
- HGFM
- YggdrasilLocal
- ClaimTransmuter
- StatusVector
- ArtifactForge
- ArchitectureAI7
- Ω-DeepTech Intelligence Forge
- Ω-ECC-T / Error Correction Codes de Tristan
- Ω-PDF-HYPERGRAPH-GITHUB-T / AIT-Frédéric
- Ω-WIKI-T∞ / WikiForge-T R0.1 Wikipedia extraction kernel
- Ω-WIKI-T∞ / WikiForge-T R0.2 repository-theory hypergraph builder

Coded candidate:

- Ω-HYPERKNOWLEDGE-T∞ R0.3 knowledge-cell, evidence-audit, contradiction, temporal-transition, and P0-P6 action-queue MVP

Crystallizable modules:

- Ω-QUATERNION-CRYSTAL-T
- Ω-LOGEXP-MORPH-T∞² R0.3
- FractalLC
- NavierTardif
- FFWT-HGFM
- CanonGenome
- TRL_M
- ImpactDashboard
- HyperParityGraph-T
- Syndrome-CVCD
- BayesDecoder_T
- PDF Rosette Extractor
- Claim-Evidence-Residue Graph
- Drive↔GitHub OAK Sync
- Exact citation-entry parsing and Citoid enrichment
- Cross-language claim alignment and contradiction detection
- Citation-safe multilingual generation
- GitHub-wide incremental theory absorption and semantic deduplication
- External source enrichment for each theory node through Wikipedia, Wikidata, DOI, ISBN, and PMID
- Unit-aware equations and calibrated measurement records
- Independent replication and stale-status detection

Exploratory branches stay labeled as exploratory until proven, simulated, or experimentally validated.
