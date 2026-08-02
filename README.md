# TFUGA / SAGE-TRISTAN

**Status:** v0.3 publication scaffold, derived from *Univers mathematique TFUGA / SAGE-TRISTAN v0.1 + Omega3-Omega6*.

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
- `OAKGate R0.2`: deterministic evidence, uncertainty, provenance, execution, privacy, attribution, IP, Markdown, SARIF, and GitHub guardrail for claim promotion and publication.
- `Ω-DeepTech Intelligence Forge`: OAK-safe layer for deeptech signals -> IP triage -> prototype tasks -> revenue routing -> GitHub artifacts.
- `Ω-ECC-T`: OAK-safe error-correction lab: Hamming(7,4), channel models, Syndrome-CVCD, HyperParityGraph-T, M⁻ hooks, and deterministic OAKBench.
- `Ω-PDF-HYPERGRAPH-GITHUB-T`: OAK-safe universal absorber for PDF/ZIP/text/code corpora -> chunks -> claim candidates -> HGFM/CVCD hypergraph -> GitHub-ready artifacts.
- `Ω-WIKI-T∞ / WikiForge-T`: read-only multilingual Wikipedia reader -> revision-pinned articles -> claim candidates -> citation/source links -> OAK manifests -> reproducible reports.

## Repository structure

```text
docs/          Manifest, roadmap, canon analysis, publication plan.
schemas/       JSON schemas for DCT++, research cards, HGFM, WikiForge, OAK claims, and rule packs.
rules/         Domain and product OAKGate policies.
sage_tristan/  Minimal Python engine for scoring, cards, status, HGFM, claims, AI-7 traces.
oakgate/       Executable claim model, gates, U², provenance, Markdown scanner, SARIF, and CLI.
omega_deeptech_forge/ Minimal OAK-safe deeptech/IP/revenue triage engine.
ecc_tristan/   Minimal Ω-ECC-T executable lab for error correction, OAK, and M⁻.
omega_prof_poly_t/ Omega absorb systems, including the universal corpus absorber.
omega_wiki_t/  Ω-WIKI-T∞ multilingual evidence compiler and citation-preserving translation guard.
tests/         Unit, adversarial, and integration tests for the executable core.
examples/      Example branches, DCT++ packets, WikiForge demos, and OAK claims.
reports/       Generated audit, provenance, SARIF, and publication reports.
```

## Scientific hygiene

Names are not proofs. A named object becomes publishable only when it has a definition, hypotheses, test, limits, status, and promotion path. Strong claims are recoded into testable models before promotion.

```text
Name makes callable. Formalization makes testable. Testing makes credible. Proof makes canonizable. Reuse makes fundamental.
```

OAKGate enforces the complementary publication invariant:

```text
myth != theory != prototype != measurement != certification != deployment
```

A passing OAKGate report is a local deterministic guardrail result, not external scientific, legal, privacy, patent, security, deployment, or institutional certification.

## Quick start

```bash
python -m pytest
python -m sage_tristan.demo
python examples/omega_deeptech_forge_demo.py
python examples/omega_ecc_t_demo.py
python examples/omega_universal_absorber_demo.py
python examples/omega_wiki_t_demo.py
```

OAKGate JSON and Markdown scans:

```bash
oakgate scan examples/oakgate_claim.json
oakgate scan examples/oakgate_claims.md --format json
oakgate scan examples/oakgate_claims.md --format github
oakgate scan examples/oakgate_claims.md --format sarif --output reports/oakgate.sarif
oakgate scan examples/oakgate_claims.md --rules rules/oakgate.deeptech.json
oakgate scan docs --recursive
oakgate hash examples/oakgate_claim.json examples/oakgate_claims.md
```

OAKGate exit codes:

```text
0 PASS
1 WARN
2 BLOCK
3 invalid input, policy, or I/O failure
```

See [`docs/OAKGATE_R0_2.md`](docs/OAKGATE_R0_2.md) for the formal scope and non-claims.

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

WikiForge-T R0.1 is extraction infrastructure, not factual certification. Wikipedia text is not proof; a citation marker is not automatically support; multilingual agreement is not automatically consensus.

Universal absorber outputs:

```text
manifest.json
chunks.jsonl
claims.jsonl
hypergraph.json
hypergraph.graphml
oak_report.json
```

WikiForge-T outputs:

```text
manifest.json
articles.jsonl
claims.jsonl
sources.jsonl
language-matrix.json
report.md
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
- OAKGate R0.2
- Ω-DeepTech Intelligence Forge
- Ω-ECC-T / Error Correction Codes de Tristan
- Ω-PDF-HYPERGRAPH-GITHUB-T / AIT-Frédéric
- Ω-WIKI-T∞ / WikiForge-T R0.1 extraction kernel

Crystallizable modules:

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
- evidence-file existence verification
- signed provenance manifests
- changed-file PR scanning
- U² calibration profiles
- false-positive benchmark corpus

Exploratory branches stay labeled as exploratory until proven, simulated, or experimentally validated.
