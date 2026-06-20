# Omega Open Data Harvester Runbook

## Purpose

Give every Tristan theory/science a repeatable open-data search path and optional bounded retrieval path.

## Search a theory

```bash
python scripts/omega_open_data_harvester.py \
  --theory omega_spectro_universe \
  --mode search \
  --max-results 5 \
  --manifest artifacts/open_data/spectro_manifest.json
```

## Retrieve with size limits

```bash
python scripts/omega_open_data_harvester.py \
  --theory omega_spectro_universe \
  --mode download \
  --max-results 3 \
  --max-bytes-per-file 25000000 \
  --out-dir artifacts/open_data/files \
  --manifest artifacts/open_data/spectro_download_manifest.json
```

## Theory keys

- `omega_math_universe`
- `omega_spectro_universe`
- `omega_materials`
- `ait_dynamics`
- `bayes_tristan`
- `hgfm`
- `bio_hgfm`
- `science_universe_atlas`
- `all`

## Source keys

- `zenodo`
- `datacite`
- `openml`
- `rcsb`
- `arxiv`

## OAK boundary

Search and retrieval do not equal validation. Every dataset must pass license review, provenance review, schema inspection, and downstream OAK tests before it can support any claim.
