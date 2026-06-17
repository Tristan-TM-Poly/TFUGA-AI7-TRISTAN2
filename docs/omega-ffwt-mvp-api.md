# Omega-FFWT-HAC-CVCD MVP API

**Status:** executable MVP, OAK-3 candidate.

This document describes the first executable Omega-FFWT-HAC-CVCD layer added to `sage_tristan/omega_ffwt.py`.

## Boundary

This implementation is intentionally conservative.

It is **not** a final FFWT theorem and does **not** claim universal superiority over FFT, DWT, PCA, SVD, or neural methods.

It is a minimal reproducible candidate pipeline:

```text
synthetic signal
→ Haar-like multiscale candidate transform
→ reconstruction
→ energy concentration
→ real HAC projection
→ CVCD summary
→ OAKScore
→ M_MINUS candidate when baseline wins
```

## Core functions

### `generate_signal(kind, length=128, seed=7)`

Deterministic synthetic signal generator.

Supported signals:

- `sine`
- `chirp`
- `step`
- `white_noise`
- `pink_like_noise`
- `fractal_like`

### `haar_ffwt_candidate(signal, levels=None)`

Returns a coefficient packet:

```python
Coefficients(
    approximation=[...],
    details=[[...], [...], ...],
    transform="haar_ffwt_candidate",
)
```

This is the first placeholder candidate for FFWT-style multiscale coefficients.

### `inverse_haar_ffwt_candidate(coefficients)`

Reconstructs the original signal from the coefficient packet.

### `energy_concentration(coefficients, keep_ratio=0.10)`

Measures how much coefficient energy is stored in the largest coefficients.

### `real_hac(x, y)`

Computes robust real projection metrics:

- covariance;
- correlation;
- coherence;
- variance of x;
- variance of y.

This is the mandatory safety baseline for future complex/quaternion/octonion/sedenion HAC experiments.

### `cvcd_summary(kind, signal)`

Returns:

- invariants;
- residues;
- hypotheses;
- M_MINUS candidates;
- OAK score.

### `run_minimal_benchmark(length=64, seed=7)`

Runs the MVP suite across the six synthetic signal families.

## Usage

```bash
python examples/omega_ffwt_demo.py
```

or:

```bash
python -m sage_tristan.omega_ffwt
```

## Tests

```bash
python -m pytest tests/test_omega_ffwt.py
```

## OAK interpretation

Current promotion ceiling: `OAK-3`.

It can reach `OAK-4/OAK-5` only after:

1. the candidate transform is compared to stronger baselines;
2. results are stored in reports;
3. failures are recorded in `m_minus/`;
4. claims remain local to tested datasets;
5. hyperalgebraic extensions return real projection and defect metrics.

## Next executable upgrades

1. Add result export to `reports/omega_ffwt_minimal_benchmark.json`.
2. Add simple compression/reconstruction after coefficient thresholding.
3. Add complex phase-coherence metrics with real projection.
4. Add quaternion commutator defect metrics.
5. Add octonion associator defect metrics.
6. Add explicit M_MINUS writer when baselines win.
