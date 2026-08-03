# Ω-SCI-PATENT-QC-DIGEST-T Source v0.4

This branch adds a compact runnable source kernel in GitHub.

## Run locally

```bash
cd projects/qc_scipatent_digest
python -m pip install -e .
python -m pytest -q
python -m qc_scipatent_digest.cli plus-ultra --out outputs/plus_ultra_v04
```

## What it does

- loads offline science/patent fixtures;
- creates CVCD digests;
- scores OAK dimensions;
- builds a small hypergraph;
- detects candidate science-IP bridges;
- generates opportunity candidates;
- writes JSON and Markdown outputs;
- keeps OAK-IP warnings attached to generated outputs.

## Why this matters

The previous artifact was a complete local package. This v0.4 source kernel makes the project directly reusable from GitHub and ready for CI, PR review, and expansion.

## Next expansion

- replace fixtures with adapters for OpenAlex/Crossref/CIPO CSV;
- add entity-resolution module;
- add SQLite/dashboard exports;
- convert opportunities into GitHub issues with OAK labels;
- keep private/live data outside public GitHub until reviewed.
