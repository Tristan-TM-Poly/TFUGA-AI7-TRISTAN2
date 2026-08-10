# Ω-CHATMEM-HGFM-T∞ — Cross-Conversation Protocol

## Goal

Make all future accessible ChatGPT conversations capable of joining one persistent Tristan memory hypergraph without requiring a full export.

## Bootstrap in a new conversation

When the conversation materially concerns Tristan's systems, theories, applications, GitHub work, prior decisions, or continuing research:

1. Recover `CHATMEM_GLOBAL_POINTER.json` from ChatGPT Library when available.
2. Recover `CHATGPT_CONTEXT_LIVE.md` and/or the smallest relevant HGFM neighborhood.
3. Use personal chat-history context as a supplementary signal, never as the sole source of truth.
4. Identify the new conversation as a new `ConversationSession` node with source type `chatgpt_active_context`.
5. Work normally using the recovered canonical context.

## Checkpoint in that conversation

At a substantive milestone, or when the user requests memory/canonization:

1. Extract only durable information.
2. Classify sensitivity and epistemic status.
3. Deduplicate against canonical HGFM nodes.
4. Create delta nodes/hyperedges/provenance.
5. Link the checkpoint to the previous checkpoint with `continues`.
6. Link changed canonical items with `supersedes` or `updates` rather than deleting history.
7. Run OAK privacy/provenance/structural checks.
8. Promote only PUBLIC derived artifacts to public GitHub.
9. Update the Library capsule and `CHATMEM_GLOBAL_POINTER.json` after successful promotion.

## Cross-chat identifiers

Each checkpoint should include:

- `checkpoint_id`
- `checkpoint_sequence`
- `capture_epoch`
- `source_type = chatgpt_active_context`
- `conversation_session_id` when available, otherwise deterministic hash
- `previous_checkpoint`
- `source_hashes`
- `touched_systems`
- `oak_status`
- `public_derivation_only`
- `raw_transcript_committed = false`

## Retrieval priority

Use the smallest sufficient context in this order:

1. Exact canonical node / relevant subgraph.
2. Latest system-specific capsule.
3. Global live capsule.
4. ChatGPT reference-chat-history/personal context as supplementary context.
5. Historical export only when backfill is required.

## Invariant

A new conversation is not a new memory universe.

`new active chat → bootstrap global pointer → recover subgraph → work → checkpoint delta → OAK → update pointer`

## Hard boundary

This protocol does not create a background listener for chats that are closed, inaccessible, deleted, temporary, or not exposed to the assistant. It guarantees cross-conversation continuity when a future conversation is active and the relevant tools/context are available.
