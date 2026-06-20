# AIT-Universe Folder Engine Runbook

## Purpose

Generate a bounded hypergraph/fractal/mycelial folder universe as an inspectable artifact.

## Safe default

```bash
python scripts/ait_universe_folder_engine.py \
  --root artifacts/AIT-Universe \
  --domain-pack configs/ait_universe_seed_pack.json \
  --max-depth 2 \
  --branching 3 \
  --node-limit 80 \
  --force
```

## Controls

- `--max-depth`: fractal zoom depth.
- `--branching`: children per node.
- `--node-limit`: absolute cap.

## Inspect outputs

```text
artifacts/AIT-Universe/Meta-Hypergraph/meta.json
artifacts/AIT-Universe/Meta-Hypergraph/META_HYPERGRAPH.md
artifacts/AIT-Universe/ait_universe_trace.json
```

## OAK status

- OAK-3: definitions and generator.
- OAK-4: CI execution and artifact production.
- OAK-5: artifact inspection across seed packs.
