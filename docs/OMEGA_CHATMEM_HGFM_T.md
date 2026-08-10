# Ω-CHATMEM-HGFM-T∞ — Conversation Memory Hypergraph

Status: **MVP / OAK-safe structural compiler**

## Purpose

Ω-CHATMEM-HGFM-T∞ converts an authorized ChatGPT export into a derived,
versioned and queryable fractal-mycelial hypergraph. It is designed for the
Tristan research stack, but the implementation is intentionally deterministic
and standard-library-only.

It does not scrape ChatGPT, bypass authentication, or claim hidden access to
conversation history. Exhaustive ingestion begins from an official export or
another explicitly supplied source.

## Architecture

```text
ChatGPT export
  -> parser / normalizer
  -> secret redaction + sensitivity classification
  -> message provenance
  -> deterministic extraction
  -> HGFM nodes + typed hyperedges
  -> ImportanceTensor
  -> epistemic classification
  -> memory candidates
  -> OAK structural/privacy gate
  -> CHATGPT_CONTEXT + MEMORY_CAPSULE
  -> topic recall
```

### Memory tiers

```text
native ChatGPT memory  ⊂  compact context capsule  ⊂  external HGFM memory
```

The external graph keeps detail and provenance. The context capsule keeps only
the highest-signal working set. Native memory should contain only durable,
cross-session invariants.

## Public-repository policy

This repository is public. Therefore this implementation does **not** commit
raw ChatGPT transcripts. The generated output is intended to be reviewed and
classified before publication. Secret-like tokens are redacted before derived
text is written.

For private transcripts, use a private storage/repository layer and publish
only explicitly approved derived artifacts.

## CLI

```bash
python -m omega_chatmem_hgfm_t sync tests/fixtures/chatgpt_export_minimal.json /tmp/chatmem
python -m omega_chatmem_hgfm_t oak /tmp/chatmem
python -m omega_chatmem_hgfm_t recall /tmp/chatmem "CHATMEM"
python -m omega_chatmem_hgfm_t capsule /tmp/chatmem
```

Repository CLI wrapper:

```bash
python scripts/omega-chatmem sync conversations.json memory-private/
```

The package is also directly executable with `python -m omega_chatmem_hgfm_t`.

## Output contract

```text
output/
  manifest.json
  hgfm/
    nodes.jsonl
    hyperedges.jsonl
    provenance.jsonl
  indexes/
    concepts.json
    conversations.json
  candidates/
    memory_candidates.jsonl
  reports/
    oak_report.json
  canon/
    CHATGPT_CONTEXT.md
    MEMORY_CAPSULE.md
    MASTER_MEMORY_INDEX.md
```

## Current extraction scope

The MVP extracts:
- conversations;
- messages;
- Ω systems;
- acronym-style concepts;
- GO commands;
- displayed equations;
- high-signal decisions/actions;
- provenance and content hashes.

Future rounds can add LLM-assisted claim/evidence extraction, semantic
embeddings, contradiction graphs, cross-repository links, temporal
supersession, M+/M− stores, and active Context Compiler routing. Those future
layers must preserve the same provenance and OAK contract.

## OAK limitations

The current OAK report verifies structural graph integrity, provenance
coverage, and secret-leak checks. It does not validate scientific truth,
mathematical proofs, legal claims, or the semantic correctness of every
heuristic extraction.

`PROMOTE` means structurally safe to continue, not "proven true".
