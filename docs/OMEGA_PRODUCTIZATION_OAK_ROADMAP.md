# Ω Productization Roadmap — Benchmarks, OAK reports, Datacenter MVP

This layer turns the merged Ω-VTP-T++ / Ω-DE-TensorProd∞ / Ω-ROI-OAK framework into a more product-oriented prototype.

## New pieces

| File | Purpose |
|---|---|
| `omega_vtp_t/oak_report_builder.py` | Unified OAK report object and decision builder |
| `omega_vtp_t/datacenter_thermal.py` | Datacenter thermal surrogate MVP with ROI/OAK checks |
| `benchmarks/omega_benchmarks.py` | Small reproducible benchmark suite |
| `examples/datacenter_oak_demo.py` | End-to-end datacenter OAK demo |
| `tests/test_productization_oak_datacenter.py` | Productization/datacenter tests |

## Why this matters

The framework must now prove four things repeatedly:

```text
1. residual reduced
2. invariants respected
3. cost/performance measured
4. financial decision risk-adjusted
```

The unified OAK report makes this inspectable:

```python
from omega_vtp_t import build_unified_oak_report

report = build_unified_oak_report(
    name="case",
    model={"degree": 4},
    residuals={"oak_status": "certified"},
    invariants={"oak_status": "certified"},
    finance={"decision": "pilot"},
)
print(report.decision.status)
```

## Datacenter MVP

The datacenter module is a conservative surrogate, not CFD. It estimates:

```text
PUE proxy
hotspot risk
annual savings
temperature invariants
OAK decision
```

Example:

```python
from omega_vtp_t import ThermalZoneState, estimate_optimized_zone, datacenter_thermal_oak_report

baseline = ThermalZoneState(
    rack_temperatures_c=(31, 32, 33),
    airflow_proxy=(1, 1, 1),
    cooling_power_kw=250,
    it_power_kw=1000,
)
optimized = estimate_optimized_zone(baseline, cooling_reduction_fraction=0.2)
report = datacenter_thermal_oak_report(
    baseline,
    optimized,
    electricity_cost_per_kwh=0.07,
    deployment_cost=10_000,
)
```

## Benchmarks

Run:

```bash
python benchmarks/omega_benchmarks.py
```

Initial benchmark targets:

```text
logistic Carleman residual
tensor feature count
Koopman polynomial map residual
elapsed seconds
```

## Next productization steps

```text
1. Add pyproject.toml as official package root.
2. Add CI benchmark smoke test.
3. Add JSON artifact output for OAK reports.
4. Add datacenter A/B-test measurement protocol.
5. Add real public/synthetic thermal dataset example.
6. Add battery BESS vertical after datacenter MVP stabilizes.
```

## OAK rule

```text
No product claim without residual, invariant, performance, and risk-adjusted financial evidence.
```
