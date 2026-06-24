# M_MINUS example — overclaim downgrade

```yaml
id: MMINUS-0001
failed_claim: "HGFM/FFWT/CVCD perfectly removes Raman noise with zero residue."
cause: "Performance claim stated before dataset, baseline, metrics and reproduction."
context: "Spectroscopy branch / Raman CVCD protocol."
anti_pattern: perfect_filtering_without_dataset
severity: high
guardrail: "A spectral performance claim requires dataset, baseline, metrics, uncertainty and reproduction."
repeat_detector:
  keywords:
    - "perfect"
    - "zero residue"
    - "residu zero"
    - "always beats baseline"
  regex_hint: "perfect|zero residue|residu zero"
  affected_files:
    - "docs/experiments/raman_cvcd_oak_protocol.md"
downgrade_rule:
  from_status: CERTIFIED
  to_status: SIMULATION_READY
  reason: "Claim has not been measured on real data."
next_minimal_test: "Run synthetic Raman benchmark against real ALS baseline and report peak error, SNR gain and distortion."
owner: "OAK-Validator"
created_at: "2026-06-18T19:30:00Z"
links:
  - "Issue #23"
```
