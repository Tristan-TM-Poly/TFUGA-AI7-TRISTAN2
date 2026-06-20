# Tristan Publication Atlas Runbook

## Purpose

Build OAK-safe publication dossiers connecting Tristan projects to public university, author, and research metadata.

## Offline Quebec template

```bash
python scripts/omega_tristan_publication_atlas.py \
  --scope quebec \
  --offline \
  --out-dir artifacts/publication_atlas/quebec_offline
```

## Quebec public metadata

```bash
python scripts/omega_tristan_publication_atlas.py \
  --scope quebec \
  --max-institutions 20 \
  --max-authors 3 \
  --max-works 5 \
  --top-k 50 \
  --out-dir artifacts/publication_atlas/quebec
```

## Canada public metadata

```bash
python scripts/omega_tristan_publication_atlas.py \
  --scope canada \
  --max-institutions 80 \
  --max-authors 2 \
  --max-works 4 \
  --top-k 120 \
  --out-dir artifacts/publication_atlas/canada
```

## Outputs

```text
publication_atlas_manifest.json
PUBLICATION_ATLAS.md
dossiers/<institution>/<project>__<public-author>.md
```

## OAK boundary

The atlas does not send messages, does not claim endorsement, and does not replace professor/lab/journal-specific review.
