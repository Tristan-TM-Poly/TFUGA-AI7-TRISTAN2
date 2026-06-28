# Omega AUTO2 Spectral Cleaning P0

This document materializes the next spectral cleaning P0 batch.

## Covered cards

- `spike_removal_core_algorithm_v1`
- `baseline_correction_core_algorithm_v1`
- `noise_estimation_core_algorithm_v1`

## Files

- `scripts/omega_auto2_spectral_cleaning_p0.py`
- `fixtures/omega_auto2/spectral_cleaning/valid_cleaning_spectrum.json`
- `fixtures/omega_auto2/spectral_cleaning/invalid_cleaning_spectrum.json`
- `tests/test_omega_auto2_spectral_cleaning_p0.py`

## Algorithms

### Noise estimation

Uses first-difference median absolute deviation as a deterministic synthetic baseline.

### Spike removal

Detects isolated high residual points against the neighbor interpolation estimate and replaces them with the local neighbor estimate.

### Baseline correction

Uses a simple endpoint linear baseline for P0 only.

## OAK status

This is an offline synthetic P0 foundation. It does not call external systems, process real spectra, or make scientific/regulatory claims.

## Locks

- External actions: disabled.
- Production use: disabled.
- Customer data: disabled.

## M-minus failure memory

Known failure modes captured in this P0 implementation:

- spectrum schema failure
- too few points for noise estimation
- too few points for spike removal
- axis/intensity mismatch
- zero axis range for baseline
- baseline estimation failure
