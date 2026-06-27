# FFWT-HAC-CVCD Benchmark v0.1

Issue: #88  
Status: stronger benchmark scaffold, not general superiority proof.

## Purpose

This package upgrades FFWT-HAC-CVCD from a promising exploratory signal into a more bounded benchmark scaffold.

It compares:

- FFT magnitude features;
- Haar DWT energy/sparsity features;
- FFWT-HAC multi-scale persistence features;
- FFWT+FFT hybrid features.

It reports:

- held-out classification accuracy;
- noise sweep;
- feature ablation against FFT;
- compression/reconstruction error using sparse Haar reconstruction;
- dataset/noise winners;
- M-minus limitations.

## Commands

```bash
python prototypes/omega_ffwt_hac_cvcd/run_ffwt_hac_benchmark.py \
  --noise-levels 0.0,0.05,0.10 \
  --output reports/omega-ffwt-hac-cvcd/benchmark.json \
  --markdown-output reports/omega-ffwt-hac-cvcd/benchmark.md

python -m pytest tests/test_ffwt_hac_benchmark.py
```

## Dataset modes

- `synthetic`: deterministic oscillator/spike dataset.
- `csv_adapter_fixture`: deterministic fixture that exercises real-dataset adapter logic.
- `load_csv_dataset(path)`: adapter for external CSV datasets with columns `label,x0,x1,...` or `label,values`.

The built-in fixture is not claimed as a real-world benchmark. External datasets must be supplied, cited, and versioned separately.

## OAK boundary

Do not claim general superiority over FFT/DWT/scattering/learned transforms unless the result reproduces across multiple external datasets, tasks, noise regimes, and compression settings.
