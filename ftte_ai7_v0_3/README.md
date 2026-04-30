# FTTE-AI7 v0.3

Fractal Tensor Tiling Engine v0.3 turns space-filling tiles into fractal tensor structures, graphs, LC-network exports, material metrics and DCT++ reports.

## Status

`crystallizable-software-packet`

This packet is code/test/report infrastructure. It is not a stable physical claim. Physical promotion remains blocked until measured data, uncertainty analysis, baselines, reproducibility and safety review exist.

## Core pipeline

```text
Tile -> Rule -> Tensor iteration -> Fractal -> Graph -> Metrics -> LC/material exports -> DCT++ report
```

## Core equation

```text
A_FTTE(P, alpha, Omega) = DCT++(Analyze(Graph(sigma_alpha_N^tensor o ... o sigma_alpha_1^tensor(P))))
```

## Local v0.3 run

A local artifact run generated source code, tests, outputs, Top27 catalogue, HGFM graph, LC export and DCT++ report.

```json
{
  "status": "succeeded",
  "decision": "PUBLISH_AS_CRYSTALLIZABLE_SOFTWARE_PACKET",
  "stable_canon_allowed": false,
  "tests": "passed"
}
```

## Modules

- `tiles.py`: Top27 seed catalogue.
- `rules.py`: fractal substitution masks.
- `tensor_iterate.py`: tensor/Kronecker-style iteration.
- `graph_extract.py`: cell adjacency graph extraction.
- `metrics.py`: dimension, porosity, connectivity, power score.
- `lc_mapper.py`: graph-to-LC network JSON export.
- `material_mapper.py`: coarse material effective metrics.
- `report.py`: DCT++ report writer.
- `run_all.py`: full bounded execution.

## AntiHype gate

Stable canon is explicitly disabled by default. This packet can generate physical hypotheses and prototype geometry, but it does not validate materials, superconductivity, gravity, cosmology or perpetual/negative-entropy claims.
