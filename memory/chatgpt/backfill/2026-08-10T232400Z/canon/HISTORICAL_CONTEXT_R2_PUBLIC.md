# Ω-CHATMEM-HGFM-T∞ — Historical Backfill R2 (Public Anchor)

This checkpoint upgrades the historical memory from summary-only reconstruction to a multi-source provenance layer.

## Coverage
- 78 unique conversations with exact message-level source access, deduplicated from 83 records.
- 3,634 exact messages fingerprinted.
- 196 additional conversation references from a Drive link/title registry.
- 62 prior R1 historical session records.
- 336 combined multi-source conversation records.
- Private HGFM: 4,041 nodes, 4,323 hyperedges, 3,634 message provenance records.
- 232 high-signal technical excerpts retained only in private ChatGPT Library memory.
- 30 M+ candidates and 69 M− candidates, all requiring OAK review before canonical promotion.

## Fidelity ladder
1. `message_exact` — strongest conversational provenance.
2. `title_link_only` — proves a captured conversation reference, not its message content.
3. `summary` / `recent_context_index` — reconstructed context, never represented as exact transcript.

## Privacy boundary
The public repository stores no raw transcript, private chat URL, conversation ID, or selected private excerpt.
The detailed R2 bundle is stored in ChatGPT Library and cryptographically anchored here with SHA-256 commitments.

## OAK rule
Historical conversation text proves that something was discussed or asserted. It does not prove that the assertion is scientifically, mathematically, commercially, or legally true.

## Retrieval rule
Future conversations should query the global pointer, then retrieve the smallest relevant R2 subgraph. Prefer exact-message provenance over title-only or summary-level records.
