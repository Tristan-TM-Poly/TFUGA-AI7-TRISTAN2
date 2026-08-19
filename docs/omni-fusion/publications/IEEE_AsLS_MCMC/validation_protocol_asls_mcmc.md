# Validation Protocol: AsLS-MCMC Raman Baseline Correction

## Goal

Turn the manuscript scaffold into a reproducible benchmark packet.

## Inputs

- Raman-like spectra on a fixed grid.
- Optional measured spectra with documented metadata.
- Synthetic spectra with known baselines for first validation.

## Synthetic generator

Generate each spectrum as:

```text
y(t) = baseline(t) + peaks(t) + noise(t)
```

Required variants:

1. smooth polynomial baseline,
2. spline baseline,
3. low noise,
4. high noise,
5. overlapping peaks,
6. broad peak that can be confused with baseline.

## Methods to compare

- deterministic AsLS grid search,
- AsLS-MCMC posterior median baseline,
- AsLS-MCMC posterior interval,
- at least one simple baseline reference such as polynomial fit.

## Metrics

- baseline RMSE when ground truth exists,
- corrected peak area error,
- corrected peak height error,
- posterior interval width,
- runtime,
- failure-case count.

## Reproducibility requirements

- fixed random seeds,
- committed configuration,
- generated output table,
- generated figure directory,
- environment information,
- CI smoke test.

## OAK promotion rule

The manuscript can claim a numerical result only if the number is produced by a committed script and appears in a generated artifact linked to the commit hash.
