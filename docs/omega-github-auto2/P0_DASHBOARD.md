# Omega AUTO2 P0 Dashboard

Living status board for the first Omega AUTO2 product spine.

## Current modules

| Module | Status | OAK | Tests | Issues | PR |
|---|---|---:|---|---|---|
| API Gateway | merged | OAK-3 synthetic | yes | #113-#116 | #129 |
| Usage Events | merged | OAK-3 synthetic | yes | #125-#126 | #130 |
| Spectral Core | merged | OAK-3 synthetic | yes | #127-#128 | #131 |
| P0 Integration Spine | this PR | OAK-3 candidate | yes | integration | this PR |
| Spectral Cleaning | next | OAK-1 planned | planned | TBD | TBD |
| P0 OAKBench | next | OAK-1 planned | planned | TBD | TBD |

## P0 Product Spine

```text
Request Envelope
→ API Gateway
→ Spectral Schema Validator
→ Axis Validator
→ Usage Event
→ Combined OAK Report
→ Next Action
```

## OAK rule

P0 does not claim production readiness. P0 makes the wedge testable, measurable, and composable.

## Current locks

- External actions: disabled.
- Production use: disabled.
- Customer data: not used.
- Fixtures: synthetic only.
- Billing/charging: not enabled.

## Next candidates

1. `spike_removal_core_algorithm_v1`
2. `baseline_correction_core_algorithm_v1`
3. `noise_estimation_core_algorithm_v1`
4. `spectral_benchmarks_benchmark_suite_v1`
