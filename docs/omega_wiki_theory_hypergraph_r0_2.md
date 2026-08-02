# Ω-WIKI-T∞ / WikiForge-T R0.2 — Repository Theory Hypergraph

Status: **coded candidate / OAK-safe repository absorption / not scientific certification**.

## Purpose

Absorb the repository's structured theory canon, Master Canon, and Master System Index into a traceable hypergraph that supports:

- navigation between systems, layers, risks, actions, and repository paths;
- prioritization of testable and executable nuclei;
- preservation of OAK status and negative-memory boundaries;
- JSON, JSONL, GraphML, and Markdown export;
- later enrichment from Wikipedia, Wikidata, DOI, ISBN, PMID, papers, datasets, and revision histories.

## Inputs

```text
interfaces/chatgpt-tristan-v2/data/theory-canon.json
docs/00_MASTER_CANON_TFUGA_AI7_AIT.md
MASTER_SYSTEM_INDEX.md
```

## Current result

```text
92 nodes
94 hyperedges
```

Node classes include theory systems, layers, workflow stages, risks, next actions, and repository paths. Hyperedges include explicit document structure, priority order, pipeline transitions, and a small set of curated cross-document core relations. Plain `Name: role` bullets are atomized so systems such as CVCD, DCT-Ω/DCT++, and FailureSynth retain their own provenance and definitions.

## Core spine

```text
TFUGA -> HGFM -> CVCD
            ^
            |
OAK <-> DCT-Ω / DCT++ <-> AI-7
 ^             ^
 |             |
Bayes-Tristan  FailureSynth

OAK -> AUTO² / Ω-LIN-T / FFWT-HAC-CVCD
OAK -> DeepTech Forge -> Company Revenue IP Publication OS
```

## OAK boundaries

- A theory node is a repository object, not a proven theorem or validated physical law.
- A hyperedge may be explicit from document structure or curated from cross-reading; its status is always recorded.
- The utility score is a transparent routing heuristic, not truth probability, market value, or scientific impact.
- Missing sources, counterexamples, measurements, and baselines remain residues rather than being silently filled.
- Publication, IP filing, commercialization, or sensitive decisions remain human-approved actions.

## Regeneration

```bash
omega-wiki absorb-theory \
  --canon-json interfaces/chatgpt-tristan-v2/data/theory-canon.json \
  --master-canon docs/00_MASTER_CANON_TFUGA_AI7_AIT.md \
  --system-index MASTER_SYSTEM_INDEX.md \
  --output-dir generated/omega_wiki_t/theory-canon-r0-2
```

## Next gates

1. Incremental GitHub-wide scanning with content hashes and changed-file updates.
2. Semantic entity deduplication across aliases and historical names.
3. Claim-level evidence nodes connected to tests, code, measurements, papers, and counterexamples.
4. WikiForge multilingual enrichment for each theory node.
5. Interactive hypergraph viewer with filters for domain, status, risk, utility, and next action.
6. OAK promotion rules that block canonization when evidence, tests, or provenance are missing.
