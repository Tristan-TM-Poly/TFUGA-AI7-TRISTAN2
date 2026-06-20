# Omega Open Data Harvester

`omega_open_data_harvester.py` gives each Tristan theory/science a bounded open-data search and optional download path.

It is designed for:

- Omega Math Universe
- Omega Spectro Universe
- Omega Materials
- AIT Dynamics
- Bayes-Tristan
- HGFM
- Bio-HGFM
- Science Universe Atlas

## Boundary

The harvester is OAK-safe:

- metadata is not scientific validation;
- a downloaded file is not proof that the license is correct;
- license hints require human review before redistribution;
- datasets require downstream OAK tests before claims.

## Search only

```bash
python scripts/omega_open_data_harvester.py \
  --theory omega_spectro_universe \
  --mode search \
  --max-results 5 \
  --manifest artifacts/open_data/spectro_manifest.json
```

## Download with bounds

```bash
python scripts/omega_open_data_harvester.py \
  --theory omega_spectro_universe \
  --mode download \
  --max-results 3 \
  --max-bytes-per-file 25000000 \
  --out-dir artifacts/open_data/files \
  --manifest artifacts/open_data/spectro_download_manifest.json
```

## Query override

```bash
python scripts/omega_open_data_harvester.py \
  --theory custom \
  --query "Raman spectroscopy dataset" \
  --sources zenodo,datacite,openml \
  --mode search
```

## Supported sources

- `zenodo`: metadata and direct file links when present.
- `datacite`: metadata and landing pages.
- `openml`: ML datasets with direct file links when present.
- `rcsb`: protein structure search and `.cif` structure downloads.
- `arxiv`: paper metadata only by default; article license varies, so downloads are disabled by default.

## Output manifest

The manifest includes:

- source
- query
- title
- landing URL
- download URL when available
- license hint
- size hint
- download status
- OAK residues

## Promotion path

- OAK-3: source map and harvester exist.
- OAK-4: CI search manifests generated.
- OAK-5: downloaded datasets pass license review and structural validation.
- OAK-6+: curated source registry and benchmark-specific test suites.
