# Theory canon hypergraph bundle R0.2

This directory contains a checked-in manifest, a human-readable useful-knowledge report, and a compact machine-readable core projection.

Regenerate the complete 92-node / 94-hyperedge bundle with:

```bash
omega-wiki absorb-theory \
  --canon-json interfaces/chatgpt-tristan-v2/data/theory-canon.json \
  --master-canon docs/00_MASTER_CANON_TFUGA_AI7_AIT.md \
  --system-index MASTER_SYSTEM_INDEX.md \
  --output-dir generated/omega_wiki_t/theory-canon-r0-2
```

The complete generated bundle also includes:

```text
knowledge-hypergraph.json
knowledge-hypergraph.graphml
theory-nodes.jsonl
knowledge-hyperedges.jsonl
```

OAK boundary: the graph organizes repository claims, systems, risks, priorities, and actions. It does not certify mathematical, physical, commercial, legal, or scientific truth.
