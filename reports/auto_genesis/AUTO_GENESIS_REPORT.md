# TTM Auto-Genesis OAK Report

Generated: `2026-06-29T00:02:21+00:00`

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
    "ffwt_dominant_level": 7.0,
    "ffwt_energy_entropy": 0.4476892944675947,
    "ffwt_mean_adjacent_coherence": 0.01777023413832191,
    "fractal_ratio": 50.775159863644944,
    "gamma_eff": 0.4906276597757615,
    "w0_eff": 5.016707035272575
  },
  "ground_truth": {
    "gamma_true": 0.5,
    "phi_true": 0.2,
    "w0_true": 5.0
  },
  "notes": "gamma/w0 extracted with robust physics estimator; FFWT signatures attached as CVCD evidence",
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
    "ffwt_dominant_level": 7.0,
    "ffwt_energy_entropy": 0.37484954970458956,
    "ffwt_mean_adjacent_coherence": 0.025893554181845642,
    "fractal_ratio": 93.34020535608137,
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
  "notes": "RLC parameters inferred from damped mode; FFWT multiscale evidence included",
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
    "D_ffwt_candidate_rel_error": 19.721326692252546,
    "D_rel_error": 0.07453875860404213
  },
  "extracted": {
    "D_eff": 1.6118081379061378,
    "D_ffwt_candidate": 31.081990038398544,
    "D_var_control": 1.26785985306961,
    "ffwt_active_levels": 8.0,
    "ffwt_coherence_L1_L2": 0.004552568435041948,
    "ffwt_coherence_L2_L3": 0.000540819289093824,
    "ffwt_coherence_L3_L4": 0.026688246631981466,
    "ffwt_coherence_L4_L5": 0.1710935288466098,
    "ffwt_coherence_L5_L6": 0.2132491354055563,
    "ffwt_coherence_L6_L7": 0.2405045296717783,
    "ffwt_coherence_L7_L8": 0.2619029478417726,
    "ffwt_detail_energy_L1": 0.00647157712913261,
    "ffwt_detail_energy_L2": 0.003661768197293538,
    "ffwt_detail_energy_L3": 0.0022294129586244425,
    "ffwt_detail_energy_L4": 0.0022376814451675175,
    "ffwt_detail_energy_L5": 0.0068316589213451955,
    "ffwt_detail_energy_L6": 0.024345402664201134,
    "ffwt_detail_energy_L7": 0.09754286094137218,
    "ffwt_detail_energy_L8": 0.3660252176063836,
    "ffwt_dominant_level": 8.0,
    "ffwt_dominant_relative_energy": 0.03168497407080346,
    "ffwt_energy_entropy": 0.43074824321845084,
    "ffwt_log_energy_slope": 0.63031722471434,
    "ffwt_mean_adjacent_coherence": 0.13121882516026204,
    "ffwt_reconstruction_energy": 11.552012534031448,
    "ffwt_reconstruction_energy_error": 1.8452440222001698e-15,
    "ffwt_relative_energy_L1": 0.0005602120937860627,
    "ffwt_relative_energy_L2": 0.00031698097509037576,
    "ffwt_relative_energy_L3": 0.00019298913951631706,
    "ffwt_relative_energy_L4": 0.00019370490107896397,
    "ffwt_relative_energy_L5": 0.0005913825752196491,
    "ffwt_relative_energy_L6": 0.0021074598553698916,
    "ffwt_relative_energy_L7": 0.008443798052851599,
    "ffwt_relative_energy_L8": 0.03168497407080346,
    "ffwt_residual_energy": 11.042666954167938,
    "ffwt_residual_ratio": 0.9559084983362828,
    "ffwt_total_detail_energy": 0.5093455798635202,
    "ffwt_total_energy": 11.55201253403147,
    "fractal_ratio": 48.823475781792,
    "mean_x_eff": 0.00783757224407755,
    "var_x_eff": 5.07143941227844
  },
  "ground_truth": {
    "D_true": 1.5,
    "t_obs": 2.0
  },
  "notes": "D extracted from log-gaussian physics; FFWT fractal_ratio tracked as candidate diffusion invariant",
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
