# M_MINUS Registry

This folder stores the negative memory of the TFUGA / SAGE-TRISTAN ecosystem.

`M_MINUS` is not failure as waste. It is failure as anti-regression intelligence.

## Purpose

- prevent repeated overclaims;
- preserve counterexamples;
- document benchmark losses;
- keep failed hypotheses useful;
- separate speculation from validation;
- protect the canon from unstable promotions.

## Rule

```text
No module should reach OAK-6 or higher without known failures, limits, and residues documented here.
```

## Entry format

Use one Markdown or YAML file per failure pattern.

```yaml
id: mminus_0001
date: YYYY-MM-DD
source_module: omega_ffwt_hac_cvcd
claim: "Claim that failed or became restricted"
failure_type: OVERCLAIM
truth_layer_before: T2
oak_level_before: OAK-2
counterexample: "Concrete failure, test, or contradiction"
residue_observed: "Metric or qualitative mismatch"
lesson: "What the system learned"
new_rule: "Guardrail added to prevent recurrence"
follow_up:
  - restrict domain
  - define baseline
  - add test
status: active_guardrail
```

## First guardrails

1. Do not promote a vision to a proof.
2. Do not promote a simulation to physical measurement.
3. Do not report hyperalgebraic gain without real projection and defect metrics.
4. Do not claim improvement without a baseline.
5. Do not hide benchmark losses.
6. Do not use sedenions without zero-divisor risk tracking.
7. Do not call a module canon unless it is documented, tested, and reusable.
