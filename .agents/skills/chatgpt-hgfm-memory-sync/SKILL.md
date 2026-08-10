---
name: chatgpt-hgfm-memory-sync
description: Ingest authorized ChatGPT conversation exports, connected Drive archives, conversation title/link registries, supplied transcripts, or the active conversation context actually visible to the assistant; extract durable knowledge into provenance-preserving HGFM memory, run OAK/privacy checks, version public-safe derived anchors in GitHub, keep detailed private memory in ChatGPT Library, and generate compact context capsules. Use when the user asks to preserve, recover, synchronize, recall, summarize, canonize, graph, checkpoint, continue, or backfill important information from ChatGPT conversations.
---

# Ω-CHATMEM-HGFM-T∞

Use this skill to turn authorized ChatGPT conversation data into an external, versioned memory without confusing conversation text with truth or source availability with source fidelity.

## Invariants

1. GitHub is the public-safe, versioned, auditable anchor; ChatGPT Library may hold richer private HGFM memory and context capsules.
2. The **active conversation actually visible to the assistant is an authorized source** when the user asks to capture or checkpoint it.
3. Authorized connected sources such as Google Drive may be used for historical backfill when they contain conversation archives or derived conversation registries accessible to the user.
4. Never claim access to conversations, turns, branches, deleted messages, or history that are not actually visible, supplied, exported, or retrievable through an authorized tool.
5. Never commit raw transcripts, private chat URLs, opaque conversation IDs, credentials, tokens, passwords, session cookies, private keys, sensitive personal data, or unreviewed private IP to a public repository by default.
6. Preserve provenance from every derived object back to a conversation/message identifier when safe, or to a source hash when public disclosure of identifiers is inappropriate.
7. Keep epistemic state separate from importance and source fidelity.
8. Keep M+ and M− explicit. Consult M− before regenerating a failed/rejected idea.
9. Repetition is not evidence. Summaries are not sources. Historical chat text proves discussion/assertion, not scientific truth.
10. Prefer incremental processing and the smallest relevant retrieval subgraph.
11. For GitHub writes, use a feature branch, limited scope, tests/OAK where applicable, and reviewable changes.
12. A new ChatGPT conversation is a new **session node**, not a new memory universe.
13. Never silently upgrade a weak historical source into a stronger one.

## Source-fidelity ladder

Rank historical evidence in this order:

1. `message_exact` — exact accessible message content with conversation/message provenance and source hash.
2. `title_link_only` — a captured conversation title/reference exists, but message content is unavailable.
3. `summary` / `recent_context_index` — reconstructed historical context from a summary or visible conversation index.
4. `generic_recollection` — supplementary only; never the canonical source when a stronger source exists.

When multiple sources overlap, deduplicate while retaining all provenance links. Prefer the strongest source as the canonical representation, but never erase weaker historical provenance.

Opaque ChatGPT conversation identifiers may incidentally correlate with time. Any timestamp inferred from identifier structure must be labeled **heuristic**, never treated as an official ChatGPT API contract or exact timestamp.

## Cross-conversation bootstrap

For future conversations that materially concern Tristan's systems, theories, applications, research, GitHub, prior decisions, or continuing work:

1. Recover `/Tristan/ChatGPT Memory/CHATMEM_GLOBAL_POINTER.json` from ChatGPT Library when available.
2. Recover the latest compact context and the smallest relevant HGFM subgraph.
3. Prefer R2+ `message_exact` history over title-only/summary history when available.
4. Use native reference-chat-history/personal context only as supplementary context; canonical GitHub/Library memory remains authoritative for stored state.
5. Represent the active conversation as a new `ConversationSession` node with `source_type=chatgpt_active_context`.
6. Work using the recovered canonical state.
7. At a substantive milestone, extract a **delta checkpoint** rather than rewriting earlier checkpoints.
8. Link the new checkpoint to the previous checkpoint with `continues`; use `updates`, `supersedes`, `contradicts`, and `touches_system` where applicable.
9. Run OAK privacy/provenance/structural checks.
10. Promote only reviewed PUBLIC derived artifacts to public GitHub.
11. Update `CHECKPOINT_REGISTRY.jsonl`, `CHATMEM_GLOBAL_POINTER.json`, and the ChatGPT Library capsule after successful promotion.

Cross-chat invariant:

`new active chat → global pointer → relevant subgraph → work → delta checkpoint → OAK → registry/pointer update`

This does **not** imply a background listener. Closed, deleted, temporary, unseen, or otherwise inaccessible chats are not claimed as captured.

## Historical backfill modes

### GO CHATMEM-BACKFILL-MAX — multi-source historical reconstruction

Use when the user wants the strongest possible reconstruction of older ChatGPT work from connected sources.

1. Discover authorized historical sources across ChatGPT Library, connected Drive/Dropbox when relevant, existing GitHub memory anchors, supplied files, and accessible prior-context summaries.
2. Prioritize exact conversation archives such as `all_conversations.json`, `conversations.json`, or per-conversation structured JSON.
3. Parse exact conversations and messages; deduplicate exact duplicate conversations before counting or building canonical nodes.
4. Fingerprint exact messages with SHA-256. Keep raw transcript text private by default.
5. Discover title/link registries separately. Treat them as `title_link_only`, not message evidence.
6. Import prior summary/index backfills as weaker provenance instead of discarding them.
7. Build a unified conversation registry, timeline, system/concept index, message provenance graph, high-signal memory candidates, M+ candidates and M− candidates.
8. Deduplicate overlapping source records while preserving every provenance edge.
9. Keep detailed graph/message-derived excerpts in private ChatGPT Library unless the user explicitly chooses a private repository or another safe store.
10. Publish to public GitHub only aggregate counts, public-safe technical indexes, OAK reports, schemas/capsules and cryptographic commitments to private artifacts.
11. Record coverage gaps explicitly. `HIGH_COVERAGE` is not `EXHAUSTIVE`.
12. Update the global pointer only after OAK passes and the detailed Library bundle is retrievable.

Pipeline:

`source discovery → fidelity classification → normalize → exact dedup → message hashing → HGFM → cross-source reconciliation → M+/M− candidates → OAK → private Library bundle → public GitHub commitments → global pointer`

### Export/backfill mode

Use an official export or supplied transcript when the user provides a direct historical source.

`export/transcript → normalize → provenance → extract → HGFM → OAK → M+/M− → canon → capsule`

Use `python -m omega_chatmem_hgfm_t sync <input.json> <output-dir>` or the repository wrapper `python scripts/omega-chatmem sync <input.json> <output-dir>`.

Do not assume a globally installed `omega-chatmem` executable unless installation has been verified.

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
9. Historical backfills may extend coverage before the capture epoch but are not a prerequisite for memory after it.
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
`continues`, `touches_system`, `same_conversation_as`, `stronger_source_for`.

## OAK promotion contract

`PROMOTE` means the generated graph passed structural/provenance/privacy gates. It does **not** mean a scientific or mathematical claim is true.

For historical backfills additionally verify:

- exact duplicates were not double-counted;
- every exact message provenance has a source hash;
- title-only records do not claim message-level content;
- summary records do not claim transcript fidelity;
- raw transcripts/private URLs/private conversation IDs/private excerpts are absent from public GitHub;
- private bundle cryptographic commitments are recorded when detailed memory remains private;
- coverage gaps and heuristic timestamps are explicitly labeled;
- M+ and M− outputs remain candidates until separately reviewed.

## ChatGPT-facing memory

Use three layers:

1. **GitHub public-safe HGFM anchor** — versioned counts, schemas, public context, OAK reports and hashes.
2. **ChatGPT Library private HGFM** — detailed historical registry, message provenance, selected technical memory, M+/M− candidates and retrieval indexes.
3. **Native ChatGPT memory/history** — supplementary durable preferences/context, not an exhaustive database.

Keep raw transcripts, sensitive context, private URLs/IDs, large theory bodies, transient PR state and detailed private evidence out of public GitHub.

## Commands

- `GO CHATMEM-LIVE`
- `GO CHATMEM-CHECKPOINT`
- `GO CHATMEM-BOOTSTRAP`
- `GO CHATMEM-BACKFILL-MAX`
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

Maximize recoverable useful knowledge × provenance × source fidelity × correctness × reuse, while minimizing noise × duplication × privacy risk × stale context × retrieval cost.
