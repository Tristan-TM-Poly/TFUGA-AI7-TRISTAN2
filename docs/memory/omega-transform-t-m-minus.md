# Ω-TRANSFORM-T M⁻ — Negative Memory

This file records OAK failures, limits and anti-overclaiming rules for the transform branch.

## M⁻-001 — Weighted FFWT can degrade reconstruction

Observation:

```text
Multiplying Haar coefficients by heuristic fractal fertility weights and then
feeding them directly into the inverse transform can worsen reconstruction.
```

Why:

```text
The inverse Haar transform expects coefficients in the original coefficient
space. If heuristic weights distort those coefficients, reconstruction error can
increase even when the weights are semantically interesting.
```

Rule:

```text
Use fertility as a selector or score first. Treat coefficient distortion as a
separate measured experiment.
```

Implemented correction:

```text
omega_transform_t/selection.py
```

The new `fertility_select_coeffs` operator scores coefficients with fertility
but reconstructs from original, unwarped coefficients.

## M⁻-002 — Reconstruction is not the only useful objective

Observation:

```text
Plain amplitude thresholding can beat fertility selection on sparse reconstruction.
```

Rule:

```text
Do not claim FFWT superiority from reconstruction alone.
```

Better task targets:

- denoising;
- anomaly scoring;
- spectroscopy peak detection;
- RLC resonance signatures;
- multichannel coherence;
- classification;
- stability under perturbation.

## M⁻-003 — Synthetic OAKBench is not proof

Rule:

```text
Synthetic benchmarks are gates, not theorems.
```

A transform becomes stronger only when it wins on external datasets or produces
reproducible invariants/residues under perturbation.
