# Validation Receipt R0.4

Local validation before GitHub publication:

- 12 R0.4 tests;
- deterministic portfolio generation;
- independent oracle verification;
- exact fallback for every seed family;
- unresolved queue exposed when only one attempt is permitted;
- SHA-256 tamper detection;
- report and receipt JSON Schemas;
- deterministic benchmark comparison.

Canonical benchmark target:

```text
problem_budget: 4096
families: 17
max_attempts_per_problem: 2
permanent_total_cap: null
expected status: CERTIFIED_SYNTHETIC_PROBLEM_RESOLUTION_FIXTURES_R0_4
```

The receipt certifies only encoded software fixtures and invariants.
