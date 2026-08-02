# Ω-SOLID-T∞ R0.1 — OAK crystallization report

## Scope delivered

- dependency-free Python package;
- canonical `SolidGenome-T` model;
- 12 encoded material archetypes;
- JSON Schema Draft 2020-12;
- material hypergraph with JSON and GraphML outputs;
- CVCD comparison signature;
- defect interaction graph and DefectTensor-T;
- PhaseGraph-T path engine;
- elasticity, mixture, Hall–Petch, Gibson–Ashby, thermal strain and fracture baselines;
- composable energy functional with exploratory-term labeling;
- calibration and uncertainty utilities;
- inverse-design ranking compiler;
- eight-gate OAK report;
- adaptive streamed candidate frontier with no permanent total-addition ceiling;
- disk-backed deduplication, checkpoints, M⁺ and M⁻ ledgers;
- CLI, example, CI workflow and documentation.

## Validation performed

```text
python -m compileall -q omega_solids_t
python -m pytest -q tests/test_omega_solids_t.py
python -m omega_solids_t.cli atlas --output-dir generated/atlas
python -m omega_solids_t.cli frontier --work-items 250 --initial-batch 16 --quality-floor 0.0 --output-dir generated/frontier
python examples/omega_solids_demo.py
```

Observed local result before publication:

- 57 tests passed;
- 12 complete analysis bundles generated;
- 250/250 candidates streamed and accepted in the explicit frontier smoke experiment;
- adaptive batch expanded from 16 to 512;
- canonical fingerprint defect found during the first test pass and corrected;
- no permanent total-candidate constant exists in the lazy source or controller.

## M⁻ captured during development

### Numeric canonicalization mismatch

Initial fingerprints differed after JSON round-trip because Python integers and restored floats compare equal but serialize differently (`1000` versus `1000.0`). The fingerprint layer now recursively canonicalizes finite numeric values before hashing.

This is retained as negative knowledge because provenance and deduplication systems can silently fork when semantically equal numeric values have different lexical representations.

## Remaining scientific limits

- archetype values are illustrative, not authoritative materials datasets;
- no atomistic, phase-field, DEM or finite-element solver is bundled in R0.1;
- defect interaction inference is heuristic and explicitly labeled;
- CVCD signatures need task-specific weighting and external validation;
- JSON Schema cannot enforce all cross-field sums, so runtime validation remains required;
- “unbounded” describes architecture without an arbitrary permanent total-count ceiling, not physically infinite execution;
- safety, fabrication, medical, structural and regulatory use remain outside certification scope.

## Next crystallization

1. CIF/POSCAR adapters and explicit unit conversions.
2. XRD/Raman/FTIR/SEM/EBSD/tomography characterization adapters.
3. Phase-field, DEM, FEA and atomistic simulation bridges.
4. FFWT-Solid image and signal benchmark.
5. Ω-3DP-T manufacturability and coupon generation.
6. Traceable external material datasets with license/provenance gates.
7. Active-learning experiment selection driven by uncertainty reduction.
