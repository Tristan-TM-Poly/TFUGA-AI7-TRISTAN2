# Ω-WIKI-T∞ / WikiForge-T R0.1

Status: **coded extraction scaffold / read-only / not factual verification**.

## Purpose

WikiForge-T turns one Wikipedia topic into a multilingual, revision-pinned evidence bundle:

```text
topic
→ canonical page + QID
→ interlanguage mappings
→ revision-pinned HTML
→ sections + paragraphs
→ claim candidates
→ reference markers + external source links
→ OAK manifest
→ JSONL + Markdown report
```

The package is independent from Wikimedia Foundation and is not an official Wikipedia product.

## Anti-bullshit boundary

- Wikipedia text is not proof.
- A citation marker does not prove that its source supports the sentence.
- An external link is not automatically reliable.
- Similar wording across languages is not automatically independent consensus.
- Translation fluency is not semantic fidelity.
- R0.1 extracts **claim candidates**; it does not certify them.

## Commands

```bash
omega-wiki read "Mécanique quantique" --lang fr
omega-wiki languages "Mécanique quantique" --lang fr
omega-wiki compile "Mécanique quantique" --lang fr --langs en,de,ja --output-dir generated/q944
omega-wiki compile "Mécanique quantique" --lang fr --langs all --max-languages 20 --output-dir generated/q944-atlas
omega-wiki audit generated/q944
```

Set `--max-languages 0` only for an intentionally unlimited run. Wikimedia access remains sequential and throttled.

## Outputs

```text
generated/q944/
├── manifest.json
├── articles.jsonl
├── claims.jsonl
├── sources.jsonl
├── language-matrix.json
└── report.md
```

Every article record stores its language, canonical URL, revision ID, revision timestamp, content hash, QID when available, and a license/attribution warning.

## Translation kernel

`CitationPreservingTranslator` wraps any configured backend. It fails closed when numerical, date, unit-like, or `[REF:...]` tokens disappear.

This is a minimal invariant check, not a complete translation-quality metric. R0.2 should add:

- named-entity alignment;
- negation preservation;
- modal-strength preservation;
- equation and symbol preservation;
- terminology glossaries;
- back-translation diagnostics;
- human-review packets.

## R0.1 limitations

1. Reference-to-sentence alignment is coarse: an inline marker attaches the article's extracted source-link set to the claim candidate.
2. Section-to-paragraph mapping is approximate because the compact HTML extractor does not yet preserve a complete DOM tree.
3. Source metadata, source type, independence, retraction state, and entailment remain unverified.
4. Cross-language semantic alignment and contradiction detection are future gates.
5. Templates, tables, math, infoboxes, media captions, and complex references require richer Parsoid handling.

## Next OAK gates

### R0.2 — Citation graph

- Parse each bibliography entry into a stable citation record.
- Resolve DOI, ISBN, PMID, QID, archive URL, author, publication, and date.
- Associate each inline marker with its exact bibliography entry.
- Retrieve source passages only where legally and technically permitted.
- Classify support as direct, partial, contradictory, inaccessible, or unresolved.

### R0.3 — Multilingual claim alignment

- Align claims by QID/entity graph, dates, quantities, embeddings, and terminology.
- Preserve unique-language knowledge instead of forcing false equivalence.
- Detect numerical, chronological, causal, and modal contradictions.
- Measure source independence to avoid copied-language pseudo-consensus.

### R0.4 — Citation-safe generator

Generated factual sentences must carry one or more `claim_id` values. Unsupported sentences must be removed or explicitly marked as inference/hypothesis.

## Safety and API hygiene

- Read-only by default.
- Identifiable User-Agent.
- Sequential throttled requests.
- Bounded retries with exponential backoff.
- No automated editing or publication.
- No claim of Wikimedia affiliation.
- Imported content retains source-specific attribution and license obligations.
