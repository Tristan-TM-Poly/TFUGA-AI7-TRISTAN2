# Omega AUTO2 P0 Dashboard

Living status board for the first Omega AUTO2 product spine.

## Current modules

| Module | Status | OAK | Tests | Issues | PR |
|---|---|---:|---|---|---|
| API Gateway | merged | OAK-3 synthetic | yes | #113-#116 | #129 |
| Usage Events | merged | OAK-3 synthetic | yes | #125-#126 | #130 |
| Spectral Core | merged | OAK-3 synthetic | yes | #127-#128 | #131 |
| P0 Integration Spine | merged | OAK-3 synthetic | yes | integration | #132 |
| Spectral Cleaning | merged | OAK-3 synthetic | yes | cleaning batch | #135 |
| P0 OAKBench / M-minus | merged | OAK-3 synthetic | yes | benchmark registry | #137 |
| Demo Pack P0 | this PR | OAK-3 candidate | yes | demo report | this PR |
| Review Pack P0 | next | OAK-1 planned | planned | TBD | TBD |

## P0 Product Spine

```text
Request Envelope
→ API Gateway
→ Spectral Schema Validator
→ Axis Validator
→ Spectral Cleaning
→ Usage Event
→ Combined OAK Report
→ OAKBench Synthetic Report
→ Demo Pack Before/After Report
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

1. `review_pack_p0_v1`
2. `before_after_markdown_report_v1`
3. `mminus_registry_expansion_v1`
4. `spectral_benchmarks_expansion_v1`
