# Ω-TRANSFORM-T Roadmap — FWT / FFWT / FFWT-N

This roadmap turns the current MVP into a falsifiable research and prototype program.

## Current MVP

- Haar FWT 1D with exact reconstruction.
- FFWT heuristic fertility weights.
- FFWT-N recursive embedding and multichannel coherence.
- OAKBench sparse reconstruction comparison.
- Unit tests for reconstruction, metrics and multichannel coherence.

## M⁻ already discovered

The naive FFWT fertility weighting can lose to plain FWT on sparse reconstruction. This is useful negative memory:

```text
Do not claim FFWT > FWT globally.
Optimize and test FFWT on tasks where fractal persistence is expected to matter.
```

## Phase 1 — Baseline hardening

- Add Daubechies/Symlet-like filters or optional PyWavelets adapter.
- Add deterministic synthetic datasets:
  - smooth periodic;
  - chirp;
  - burst/anomaly;
  - fractal Brownian-like;
  - multi-channel coupled/noisy.
- Add baseline comparisons:
  - FFT compression;
  - DCT compression;
  - SVD for matrices/images;
  - simple time-domain thresholding.

## Phase 2 — Task OAKBench

Measure FFWT where it may actually win:

1. anomaly detection;
2. denoising;
3. classification;
4. spectroscopy peak detection;
5. RLC resonance signatures;
6. multichannel coherence;
7. stability under perturbation.

Every benchmark must report:

```text
metric_value
baseline_value
delta
residual
runtime
OAK verdict
M⁺ / M⁻ update
```

## Phase 3 — FFWT-N real tensorization

- Implement separable 2D image transform.
- Implement ND separable transform.
- Implement coefficient hypergraph export.
- Add inter-scale and inter-channel edges.
- Add JSON/GraphML export for HGFM/CVCD analysis.

## Phase 4 — FFWT-HAC-CVCD integration

Connect with the existing Ω-FFWT-HAC-CVCD branch:

- real covariance baseline;
- complex phase coherence;
- quaternion orientation coherence;
- octonion associator residue;
- sedenion zero-divisor risk map, always with robust real projection.

## Phase 5 — Universal Tristan Transform / Ω-UTT

Build a transform selector:

```text
T* = argmax utility(T) - error(T) - cost(T)
```

Candidate transforms:

- FFT;
- FWT;
- FFWT;
- DCT;
- SVD;
- STFT/CWT;
- graph wavelets;
- DMD/Koopman.

## Canon rule

```text
No revolution without benchmark.
```

A transform becomes canon only when it improves a measured task or reveals a reproducible invariant/residue.
