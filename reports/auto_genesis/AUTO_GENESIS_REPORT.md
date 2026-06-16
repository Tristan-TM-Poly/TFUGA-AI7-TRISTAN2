# TTM Auto-Genesis OAK Report

Generated: `2026-06-16T21:25:22+00:00`

## Verdict summary

- **CANON**: 4
- **FERTILE**: 0
- **M_MINUS**: 0

## Findings

### Theory corpus integrity

- Category: `canon`
- Status: `CANON`
- Next action: Keep theories linked to executable benchmarks and ablation reports.

```json
{
  "cvcd_files": 3,
  "ffwt_files": 3,
  "oak_files": 3,
  "theory_files": 3
}
```

### B1 — Damped oscillator

- Category: `benchmark`
- Status: `CANON`
- Next action: Promote to regression test and compare against FFT/STFT/CWT baselines.

```json
{
  "errors": {
    "gamma_rel_error": 0.018744680448439504,
    "w0_rel_error": 0.003341407054514398
  },
  "extracted": {
    "gamma_eff": 0.4906276597757615,
    "w0_eff": 5.016707035272575
  },
  "ground_truth": {
    "gamma_true": 0.5,
    "phi_true": 0.2,
    "w0_true": 5.0
  },
  "notes": "gamma and w0 extracted from analytic envelope + FFT/phase fusion",
  "oak_score": 93.89569562485231
}
```

### B2 — RLC underdamped

- Category: `benchmark`
- Status: `CANON`
- Next action: Promote to regression test and compare against FFT/STFT/CWT baselines.

```json
{
  "errors": {
    "Q_rel_error": 0.04979126153379131,
    "alpha_rel_error": 0.051486879050975064,
    "omega0_rel_error": 0.0008679791430694236,
    "wd_rel_error": 0.0011325706701640222
  },
  "extracted": {
    "Q_eff": 6.787205274758584,
    "alpha_eff": 0.36802040766789273,
    "omega0_eff": 4.995660104284652,
    "wd_eff": 4.982085994549
  },
  "ground_truth": {
    "C_true": 0.04,
    "L_true": 1.0,
    "Q_true": 7.142857142857143,
    "R_true": 0.7,
    "alpha_true": 0.35,
    "omega0_true": 5.0,
    "wd_true": 4.987734956871706
  },
  "notes": "RLC parameters inferred from damped oscillatory mode",
  "oak_score": 89.91803274005001
}
```

### B3 — Diffusion 1D

- Category: `benchmark`
- Status: `CANON`
- Next action: Promote to regression test and compare against FFT/STFT/CWT baselines.

```json
{
  "errors": {
    "D_rel_error": 0.07453875860404213
  },
  "extracted": {
    "D_eff": 1.6118081379061378,
    "D_var_control": 1.26785985306961,
    "haar_detail_energy_L1": 0.003800438194022626,
    "haar_detail_energy_L2": 0.0010340774014629454,
    "haar_detail_energy_L3": 0.00030486504984560364,
    "haar_detail_energy_L4": 0.00014919051027407424,
    "haar_detail_energy_L5": 0.0002142651269254907,
    "haar_residual_energy": 0.3603350606246709,
    "mean_x_eff": 0.00783757224407755,
    "var_x_eff": 5.07143941227844
  },
  "ground_truth": {
    "D_true": 1.5,
    "t_obs": 2.0
  },
  "notes": "D extracted from robust spatial variance, using Var[x]=2Dt",
  "oak_score": 88.54612413959579
}
```

## Improvement queue

- **P0** — Freeze B1 — Damped oscillator as regression benchmark
  - Rationale: CANON OAK score reached; future code must not regress this result.
  - Suggested file: `tests/test_omega_max_benchmark.py`
- **P0** — Freeze B2 — RLC underdamped as regression benchmark
  - Rationale: CANON OAK score reached; future code must not regress this result.
  - Suggested file: `tests/test_omega_max_benchmark.py`
- **P0** — Freeze B3 — Diffusion 1D as regression benchmark
  - Rationale: CANON OAK score reached; future code must not regress this result.
  - Suggested file: `tests/test_omega_max_benchmark.py`
- **P0** — Replace Haar/analytic surrogate with true adaptive FFWT core
  - Rationale: Current prototype is executable but not yet the full fractal wavelet transform.
  - Suggested file: `core/ffwt_core.py`
- **P1** — Add baseline comparison suite: FFT, STFT, DWT/CWT, PCA/SVD
  - Rationale: OAK requires measurable gains against standard methods.
  - Suggested file: `prototypes/baselines.py`
- **P1** — Add ablation matrix R/C/H/O/S16
  - Rationale: Hyperalgebraic claims must beat simpler algebras before canonization.
  - Suggested file: `prototypes/algebra_ablation.py`

## Guardrails

This workflow is intentionally guarded: it writes reports only. It does not autonomously rewrite source code.
Future self-modifying behavior must be implemented through pull requests, tests, and explicit review gates.
