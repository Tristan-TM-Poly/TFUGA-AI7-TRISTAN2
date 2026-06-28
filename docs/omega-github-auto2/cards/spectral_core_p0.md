# Omega AUTO2 Spectral Core P0

This document materializes the spectral core P0 batch from issues #127 and #128.

## Covered cards

- #127 — `axis_validation_core_algorithm_v1`
- #128 — `schema_validation_core_algorithm_v1`

## Files

- `scripts/omega_auto2_spectral_core_p0.py`
- `fixtures/omega_auto2/spectral_core/valid_spectrum.json`
- `fixtures/omega_auto2/spectral_core/invalid_spectrum.json`
- `tests/test_omega_auto2_spectral_core_p0.py`

## Axis validator

The axis validator checks:

- axis is a list
- axis has at least two points
- every value is finite numeric
- axis unit is allowed or warned when missing
- neighboring points are not duplicated
- axis is monotonic
- spacing summary is reported

## Spectrum schema validator

The schema validator checks:

- `spectrum_id`
- `axis`
- `intensity`
- `metadata`
- axis and intensity length match
- intensity values are finite numeric
- metadata is object-shaped

## OAK report

The script emits:

- `status`
- `schema`
- `external_actions_allowed = false`
- `production_use_allowed = false`
- `residue_report`
- `next_action`
- `generated_at`

## OAK status

This is an offline synthetic P0 foundation. It does not call external systems, process real spectra, or make scientific/regulatory claims.

## M-minus failure memory

Known failure modes captured in this P0 implementation:

- axis is not a list
- axis has too few points
- non-finite numeric values
- unsupported axis unit
- duplicate neighboring axis points
- non-monotonic axis
- axis/intensity length mismatch
- invalid intensity value
- missing or empty spectrum id
