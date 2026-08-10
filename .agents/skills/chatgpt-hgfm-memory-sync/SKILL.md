---
name: chatgpt-hgfm-memory-sync
description: Ingest authorized ChatGPT conversation exports, supplied transcripts, or the active conversation context actually visible to the assistant; extract durable knowledge into provenance-preserving HGFM memory, run OAK/privacy checks, version derived artifacts in GitHub, and generate compact ChatGPT context capsules. Use when the user asks to preserve, recover, synchronize, recall, summarize, canonize, graph, checkpoint, or continue important information from ChatGPT conversations.
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
12. A new ChatGPT conversation is a new **session node**, not a new memory universe.

## Cross-conversation bootstrap

For future conversations that materially concern Tristan's systems, theories, applications, research, GitHub, prior decisions, or continuing work:

1. Recover `/Tristan/ChatGPT Memory/CHATMEM_GLOBAL_POINTER.json` from ChatGPT Library when available.
2. Recover the latest compact context and the smallest relevant HGFM subgraph.
3. Use reference-chat-history/personal context only as supplementary context; canonical GitHub/Library memory remains authoritative for stored state.
4. Represent the active conversation as a new `ConversationSession` node with `source_type=chatgpt_active_context`.
5. Work using the recovered canonical state.
6. At a substantive milestone, extract a **delta checkpoint** rather than rewriting earlier checkpoints.
7. Link the new checkpoint to the previous checkpoint with `continues`; use `updates`, `supersedes`, `contradicts`, and `touches_system` where applicable.
8. Run OAK privacy/provenance/structural checks.
9. Promote only reviewed PUBLIC derived artifacts to public GitHub.
10. Update `CHECKPOINT_REGISTRY.jsonl`, `CHATMEM_GLOBAL_POINTER.json`, and the ChatGPT Library capsule after successful promotion.

Cross-chat invariant:

`new active chat → global pointer → relevant subgraph → work → delta checkpoint → OAK → registry/pointer update`

This does **not** imply a background listener. Closed, deleted, temporary, unseen, or otherwise inaccessible chats are not claimed as captured.

## Two ingestion modes

### Export/backfill mode

Use an official export or supplied transcript when the user wants older history reconstructed.

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
7. Emit a live checkpoint containing `checkpoint.json`, HGFM nodes/hyperedges/provenance and a compact context capsule.
8. When ChatGPT Library is available, maintain the compact global pointer/capsule there for cross-conversation retrieval.
9. Later exports may backfill history **before** the capture epoch, but are not a prerequisite for memory **after** it.
10. Never describe unseen history as captured.

## Checkpoint selection

Promote only meaningfully reusable content: canonical system/theory names, durable definitions, explicit decisions/constraints, important results with evidence, GitHub artifacts/PRs/commits, stable workflow preferences, open questions/next actions, and M− failures/contradictions/rejected hypotheses.

Avoid greetings, filler, transient phrasing, duplicated restatements, raw chain-of-thought, secrets/sensitive data, and unsupported claims promoted as facts.

## Fractal levels

- L0: source span/message/turn hash
- L1: atomic Concept/System/Equation/Decision/Action
- L2: conversation session/checkpoint graph
- L3: theory/system/project graph
- L4: global Tristan corpus
- L5: meta-architecture and cross-domain links

Traverse both downward to source evidence and upward to canonical systems.

## Canonical relation vocabulary

Use typed relations such as:

`contains`, `mentions`, `defines`, `extends`, `specializes`, `generalizes`,
`depends_on`, `derived_from`, `supports`, `contradicts`, `falsifies`, `tests`,
`implements`, `measures`, `predicts`, `explains`, `uses`, `produces`,
`supersedes`, `updates`, `duplicates`, `variant_of`, `motivates`, `blocks`,
`resolves`, `failed_because`, `next_action_for`, `commercializes`,
`patent_candidate_for`, `activates`, `constrains`, `allows_backfill`,
`continues`, `touches_system`.

## OAK promotion contract

`PROMOTE` means the generated graph passed structural/provenance/privacy gates. It does **not** mean a scientific or mathematical claim is true.

For a live checkpoint, verify every public node is PUBLIC, source hashes are valid, no raw transcript field is emitted, every hyperedge member exists, scope/capture epoch are explicit, and no inaccessible history is claimed as captured.

## ChatGPT-facing memory

Use three layers:

1. **GitHub HGFM** — detailed, versioned, auditable external memory.
2. **ChatGPT Library** — `CHATMEM_GLOBAL_POINTER.json` plus compact context capsules retrievable across conversations.
3. **Native ChatGPT memory/history** — supplementary durable preferences/context, not an exhaustive database.

Keep equations, large theory bodies, transient PR state, raw transcripts and detailed evidence external.

## Commands

- `GO CHATMEM-LIVE`
- `GO CHATMEM-CHECKPOINT`
- `GO CHATMEM-BOOTSTRAP`
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

Maximize recoverable useful knowledge × provenance × correctness × reuse, while minimizing noise × duplication × privacy risk × stale context × retrieval cost.
