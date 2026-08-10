---
name: chatgpt-hgfm-memory-sync
description: Ingest authorized ChatGPT conversation exports or supplied transcripts, extract durable knowledge into provenance-preserving HGFM memory, run OAK/privacy checks, version derived artifacts in GitHub, and generate compact ChatGPT context capsules. Use when the user asks to preserve, recover, synchronize, recall, summarize, canonize, or graph important information from ChatGPT conversations.
---

# Ω-CHATMEM-HGFM-T∞

Use this skill to turn authorized ChatGPT conversation data into an external, versioned memory without confusing conversation text with truth.

## Invariants

1. GitHub is the detailed external memory; native ChatGPT memory is only a compact durable cache.
2. Never claim access to conversations that were not supplied, exported, or available through an authorized tool.
3. Never commit raw transcripts to a public repository by default.
4. Never commit credentials, tokens, passwords, session cookies, private keys, or sensitive personal data.
5. Preserve provenance from every derived object back to conversation/message/hash.
6. Keep epistemic state separate from importance.
7. Keep M+ and M− explicit. Consult M− before regenerating a failed/rejected idea.
8. Repetition is not evidence. Summaries are not sources. Hypotheses are not proofs.
9. Prefer incremental processing and the smallest relevant retrieval subgraph.
10. For GitHub writes, use a feature branch, limited scope, tests, OAK, and reviewable changes.

## Pipeline

When given a ChatGPT export or transcript:

1. Run `omega-chatmem sync <input.json> <output-dir>`.
2. Inspect `<output-dir>/reports/oak_report.json`.
3. Stop promotion if OAK is `FAIL`.
4. Inspect `candidates/memory_candidates.jsonl`.
5. Promote only appropriate PUBLIC derived artifacts to a public repo.
6. Keep PRIVATE/SECRET/IP-sensitive raw data outside public GitHub.
7. Use `omega-chatmem recall <output-dir> "<topic>"` to retrieve a minimal subgraph.
8. Use `canon/CHATGPT_CONTEXT.md` or `canon/MEMORY_CAPSULE.md` as compact context, not as the sole source of truth.
9. When a new export arrives, rerun sync and use `omega-chatmem diff` to measure the delta.

## Fractal levels

- L0: source span/message
- L1: atomic Concept/System/Equation/Decision/Action
- L2: conversation graph
- L3: theory/system/project graph
- L4: global corpus
- L5: meta-architecture and cross-domain links

Traverse both downward to source evidence and upward to canonical systems.

## Canonical relation vocabulary

Use typed relations such as:

`contains`, `mentions`, `defines`, `extends`, `specializes`, `generalizes`,
`depends_on`, `derived_from`, `supports`, `contradicts`, `falsifies`, `tests`,
`implements`, `measures`, `predicts`, `explains`, `uses`, `produces`,
`supersedes`, `duplicates`, `variant_of`, `motivates`, `blocks`, `resolves`,
`failed_because`, `next_action_for`, `commercializes`, `patent_candidate_for`.

## OAK promotion contract

`PROMOTE` means the generated graph passed structural/provenance/privacy gates.
It does **not** mean a scientific or mathematical claim is true.

Never automatically classify a claim as `PROVEN` from language alone.

## Native-memory candidates

Only recommend native ChatGPT memory for long-lived preferences, stable goals,
persistent operating rules, and highly reused canonical names. Keep equations,
large theory bodies, transient PR state, raw transcripts, and detailed evidence
external.

## Commands

- `GO CHATMEM-INGEST`
- `GO CHATMEM-HGFM`
- `GO CHATMEM-OAK`
- `GO CHATMEM-CANON`
- `GO CHATMEM-RECALL <topic>`
- `GO CHATMEM-SYNC`
- `GO CHATMEM-MINUS`
- `GO CHATMEM-DIFF`
- `GO CHATMEM-CAPSULE`

## Success metric

Maximize recoverable useful knowledge × provenance × correctness × reuse,
while minimizing noise × duplication × privacy risk × stale context × retrieval cost.
