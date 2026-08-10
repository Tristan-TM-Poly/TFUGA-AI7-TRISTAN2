---
name: chatgpt-hgfm-memory-sync
description: Ingest authorized ChatGPT conversation exports, supplied transcripts, or the active conversation context actually visible to the assistant; extract durable knowledge into provenance-preserving HGFM memory, run OAK/privacy checks, version derived artifacts in GitHub, and generate compact ChatGPT context capsules. Use when the user asks to preserve, recover, synchronize, recall, summarize, canonize, graph, or checkpoint important information from ChatGPT conversations.
---

# Ω-CHATMEM-HGFM-T∞

Use this skill to turn authorized ChatGPT conversation data into an external, versioned memory without confusing conversation text with truth.

## Invariants

1. GitHub is the detailed external memory; native ChatGPT memory and ChatGPT Library capsules are compact retrieval layers.
2. The **active conversation actually visible to the assistant is an authorized source** when the user asks to capture or checkpoint it.
3. Never claim access to conversations, turns, branches, deleted messages, or history that are not actually visible, supplied, exported, or retrievable through an authorized tool.
4. Never commit raw transcripts to a public repository by default.
5. Never commit credentials, tokens, passwords, session cookies, private keys, or sensitive personal data.
6. Preserve provenance from every derived object back to a conversation/turn identifier or source hash.
7. Keep epistemic state separate from importance.
8. Keep M+ and M− explicit. Consult M− before regenerating a failed/rejected idea.
9. Repetition is not evidence. Summaries are not sources. Hypotheses are not proofs.
10. Prefer incremental processing and the smallest relevant retrieval subgraph.
11. For GitHub writes, use a feature branch, limited scope, tests/OAK where applicable, and reviewable changes.

## Two ingestion modes

### Export/backfill mode

Use an official export or supplied transcript when the user wants older history reconstructed.

Pipeline:

`export/transcript → normalize → provenance → extract → HGFM → OAK → M+/M− → canon → capsule`

Use `omega-chatmem sync <input.json> <output-dir>`.

### Live/current-context mode

When the user says things such as **"à partir d'ici"**, **"remember this from now on"**, **"checkpoint this chat"**, or otherwise explicitly asks to preserve the current work:

1. Treat only the conversation content actually visible in the current context as the source.
2. Establish a `capture_epoch`.
3. Do **not** wait for an export.
4. Extract only durable/high-signal information: systems, definitions, decisions, constraints, evidence, failures, artifacts, next actions and stable preferences.
5. For public GitHub, store derived PUBLIC memory only; do not publish the raw transcript.
6. Preserve source provenance with turn keys and SHA-256 hashes when exact message IDs are unavailable.
7. Emit a live checkpoint containing:
   - `checkpoint.json`
   - `hgfm/nodes.jsonl`
   - `hgfm/hyperedges.jsonl`
   - `hgfm/provenance.jsonl`
   - `canon/CHATGPT_CONTEXT_LIVE.md`
8. When ChatGPT Library is available and the user wants reusable ChatGPT memory, keep a compact current capsule there as a retrieval surface.
9. Later exports may backfill history **before** the capture epoch, but are not a prerequisite for memory **after** it.
10. Never describe unseen history as captured.

The live-memory invariant is:

`visible current context → derived checkpoint → HGFM GitHub → compact ChatGPT capsule`

not:

`assumed full ChatGPT history → GitHub`.

## Checkpoint selection

Promote a current-context item only when it is meaningfully reusable. Prefer:

- canonical system/theory names;
- durable definitions;
- explicit decisions and constraints;
- important results with evidence;
- GitHub artifacts/PRs/commits;
- stable user workflow preferences;
- open questions and next actions;
- M− failures, contradictions and rejected hypotheses.

Avoid:

- greetings and conversational filler;
- transient phrasing;
- duplicated restatements;
- raw chain-of-thought;
- secrets or sensitive data;
- unsupported claims promoted as facts.

## Pipeline for an export or supplied transcript

1. Run `omega-chatmem sync <input.json> <output-dir>`.
2. Inspect `<output-dir>/reports/oak_report.json`.
3. Stop promotion if OAK is `FAIL`.
4. Inspect `candidates/memory_candidates.jsonl`.
5. Promote only appropriate PUBLIC derived artifacts to a public repo.
6. Keep PRIVATE/SECRET/IP-sensitive raw data outside public GitHub.
7. Use `omega-chatmem recall <output-dir> "<topic>"` to retrieve a minimal subgraph.
8. Use `canon/CHATGPT_CONTEXT.md`, `canon/CHATGPT_CONTEXT_LIVE.md`, or `canon/MEMORY_CAPSULE.md` as compact context, not as the sole source of truth.
9. When a new source arrives, update incrementally and record the delta.

## Fractal levels

- L0: source span/message/turn hash
- L1: atomic Concept/System/Equation/Decision/Action
- L2: conversation/checkpoint graph
- L3: theory/system/project graph
- L4: global Tristan corpus
- L5: meta-architecture and cross-domain links

Traverse both downward to source evidence and upward to canonical systems.

## Canonical relation vocabulary

Use typed relations such as:

`contains`, `mentions`, `defines`, `extends`, `specializes`, `generalizes`,
`depends_on`, `derived_from`, `supports`, `contradicts`, `falsifies`, `tests`,
`implements`, `measures`, `predicts`, `explains`, `uses`, `produces`,
`supersedes`, `duplicates`, `variant_of`, `motivates`, `blocks`, `resolves`,
`failed_because`, `next_action_for`, `commercializes`, `patent_candidate_for`,
`activates`, `constrains`, `allows_backfill`.

## OAK promotion contract

`PROMOTE` means the generated graph passed structural/provenance/privacy gates.
It does **not** mean a scientific or mathematical claim is true.

Never automatically classify a claim as `PROVEN` from language alone.

For a live checkpoint, also verify:

- every public node is PUBLIC;
- source hashes are well formed;
- no raw transcript field is emitted;
- every hyperedge member exists;
- the checkpoint explicitly states its source scope and capture epoch;
- no claim is made that inaccessible history was captured.

## ChatGPT-facing memory

Use three layers:

1. **GitHub HGFM** — detailed, versioned, auditable source of external memory.
2. **ChatGPT Library capsule** — compact persistent file retrievable across conversations when available.
3. **Native ChatGPT memory candidate** — only durable preferences, stable goals, persistent operating rules and highly reused canonical names.

Keep equations, large theory bodies, transient PR state, raw transcripts and detailed evidence external.

## Commands

- `GO CHATMEM-LIVE`
- `GO CHATMEM-CHECKPOINT`
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
