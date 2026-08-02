# Ω-PROPULSION R0.5 Max — DiscrepancyTensor-T

## Purpose

`DiscrepancyTensor-T` compares declared observations across evidence tiers without treating agreement as proof or disagreement as an automatic verdict against either source.

A metric observation contains:

- evidence tier;
- metric name;
- numerical value;
- physical unit;
- standard uncertainty;
- SHA-256 artifact identity;
- provenance.

For adjacent available evidence tiers of the same metric and unit, the tensor computes:

```text
signed_delta = higher_value - lower_value
absolute_delta = |signed_delta|
relative_delta = signed_delta / |lower_value|
combined_standard_uncertainty = sqrt(u_lower² + u_higher²)
normalized_residual = signed_delta / combined_standard_uncertainty
```

When the combined uncertainty is zero, the normalized residual is left `null`; the software does not invent infinite certainty.

## OAK rules

1. Unit mismatches are blocked rather than silently converted.
2. Observation identifiers must be unique.
3. Values and uncertainties must be finite.
4. Standard uncertainty cannot be negative.
5. `|normalized_residual| > 2` is only a discrepancy flag under the declared uncertainty model.
6. A small normalized residual does not prove that either model is physically correct.
7. A large normalized residual does not identify which model, boundary condition, calibration or dataset is responsible.
8. No model is automatically promoted.
9. `physics_certified` remains `false`.

## CLI

```bash
omega-propulsion-r05 discrepancy-demo
```

The demonstration compares two metrics across F0 analytic and F3 vortex-proxy observations. Its numbers are deterministic fixtures, not external validation data.

## Future use

The same contract can later compare:

- BEM versus free-wake;
- free-wake versus CFD;
- CFD mesh levels;
- CFD versus wind-tunnel or tow-tank data;
- experiment versus repeated experiment;
- vehicle-level mission predictions versus telemetry.

Every future observation must retain unit, uncertainty, provenance and artifact identity.