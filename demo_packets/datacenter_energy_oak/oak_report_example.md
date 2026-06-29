# OAK Report Example — Datacenter Energy Microbenchmark

## Status

```yaml
status: example_report
scope: simulated_or_lightweight_surrogate
industrial_validation: false
CFD_replacement: false
facility_approval: not_applicable
```

## Hypothesis

A lightweight datacenter thermal/energy surrogate can help screen whether a cooling-control idea is worth deeper study by comparing baseline and optimized scenarios, measuring residuals and invariants, and producing a cautious ROI-OAK decision.

## Existing code basis

```text
omega_vtp_t/datacenter_thermal.py
examples/datacenter_oak_demo.py
```

The code defines:

- `ThermalZoneState`
- `hotspot_risk_score`
- `estimate_optimized_zone`
- `datacenter_thermal_oak_report`
- integration with `build_unified_oak_report`

## Example baseline

```yaml
baseline:
  rack_temperatures_c: [31.2, 33.4, 34.8, 32.1]
  airflow_proxy: [1.0, 0.9, 0.85, 1.1]
  cooling_power_kw: 250.0
  it_power_kw: 1000.0
  pue_proxy_formula: "(IT power + cooling power) / IT power"
```

## Example optimization scenario

```yaml
optimized_scenario:
  cooling_reduction_fraction: 0.18
  temperature_penalty_c: conservative surrogate penalty
  electricity_cost_per_kwh: 0.07
  deployment_cost: 10000.0
  verification_probability: 0.8
```

## Metrics

```yaml
metrics:
  baseline_pue_proxy: measured_from_surrogate
  optimized_pue_proxy: measured_from_surrogate
  pue_reduction: baseline_pue_proxy - optimized_pue_proxy
  hotspot_risk_score: mean_squared_excess_above_threshold
  estimated_annual_savings: expected_value_from_ROI_OAK
```

## Residual checks

```yaml
residuals:
  pue_not_improved:
    meaning: optimized scenario failed to improve PUE proxy
    threshold: near_zero
  hotspot_risk_increase:
    meaning: energy savings increased thermal risk
    threshold: near_zero
  max_temperature_excess:
    meaning: optimized scenario exceeded thermal limit
    threshold: 0.1 C tolerance
```

## Invariant checks

```yaml
invariants:
  temperature_limit:
    expected: max_temperature <= configured maximum
  it_power_preserved:
    expected: IT power unchanged in this surrogate scenario
```

## Decision logic

```yaml
decision:
  pilot_candidate:
    conditions:
      - finance decision is deploy or pilot
      - residuals certified
      - invariants certified
  no_go_m_minus:
    conditions:
      - residuals high
      - invariant violation
  research_only:
    conditions:
      - uncertain, incomplete, or not yet pilot-ready
```

## OAK interpretation

This example can support an academic discussion because it is explicit about assumptions, baseline, residuals, invariants, and verification probability.

It cannot support an industrial savings claim unless validated on real data, by qualified facility/thermal experts, with instrumentation, safety review, and a controlled pilot.

## Next academic collaboration step

```yaml
next_step:
  option_A: provide a simple anonymous/simulated thermal dataset
  option_B: choose a public benchmark or pedagogical scenario
  option_C: compare this surrogate against a stronger baseline model
  option_D: adapt the report to an energy/materials/systems course or student project
```
