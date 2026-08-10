# Ω-CHATMEM-HGFM-T∞ — bootstrap capsule

Status: **BOOTSTRAP / no private export ingested**

This repository now contains the public-safe compiler for turning explicitly
supplied ChatGPT conversations into provenance-preserving HGFM memory.

## Durable architecture

`Conversation → normalize/provenance → extract → HGFM → ImportanceTensor →
epistemic state → OAK → M+/M− candidates → GitHub canon → context capsule →
topic recall`

## Source-of-truth rule

- Detailed memory: external HGFM.
- Working context: generated `CHATGPT_CONTEXT.md`.
- Native ChatGPT memory: only durable, compact invariants and operating rules.
- Raw private transcripts: never committed to this public repository by default.

## OAK rule

Conversation ≠ memory ≠ truth. Repetition ≠ evidence. Summary ≠ source.
Hypothesis ≠ proof.

## Next ingestion

Provide an official ChatGPT export (for example `conversations.json`) to the
CLI in a private working environment, inspect the OAK report, then promote only
approved derived PUBLIC artifacts.
