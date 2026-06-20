# AIT-Universe Folder Engine

This engine is a bounded, deterministic, stdlib-only generator for recursive folder and file structures. Each folder is treated as a hypergraph node, each local `Hypergraph/` folder stores the node data, and the root `Meta-Hypergraph/` links the generated levels.

## Boundary

This engine is OAK-safe:

- generated folders are structural scaffolds, not claims;
- generated scores are heuristic placeholders, not truth;
- generated links are local structural links, not proof of relationship;
- recursion is bounded by `--max-depth`, `--branching`, and `--node-limit`.

## Quick run

```bash
python scripts/ait_universe_folder_engine.py \
  --root artifacts/AIT-Universe \
  --domain-pack configs/ait_universe_seed_pack.json \
  --max-depth 2 \
  --branching 3 \
  --node-limit 80 \
  --force
```

## Dry run

```bash
python scripts/ait_universe_folder_engine.py \
  --root artifacts/AIT-Universe \
  --max-depth 2 \
  --branching 3 \
  --node-limit 80 \
  --dry-run
```

## Generated structure

Each node folder receives:

```text
Hypergraph/
  nodes.json
  edges.json
  invariants.json
  fractal.json
  mycelium.json
  graph.hypergraph
Sublevels/
Stability/
  row.json
  residue.json
  continuum.json
README.md
```

The root receives:

```text
Meta-Hypergraph/
  meta.json
  meta.hypergraph
  meta.graphml
  META_HYPERGRAPH.md
ait_universe_trace.json
```

## Suggested OAK promotion path

- OAK-3: engine definition and seed pack exist.
- OAK-4: engine executes deterministically and CI generates artifacts.
- OAK-5: artifacts inspected across several seed packs.
- OAK-6+: external curation of domain packs and invariants.
