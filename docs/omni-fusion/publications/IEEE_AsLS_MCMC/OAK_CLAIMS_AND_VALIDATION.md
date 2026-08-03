# OAK Claims and Validation Ledger: AsLS-MCMC Raman Packet

Status: DRAFT_METHOD_SPECIFICATION.

The repository now contains a LaTeX manuscript scaffold and validation notes. It does not yet contain executable benchmark code, measured Raman data, benchmark metrics, or CI artifacts validating numerical performance.

## Claims

1. AsLS can be written as a weighted penalized least-squares baseline estimator. Status: definition.
2. MCMC can explore AsLS parameter uncertainty. Status: method hypothesis.
3. The pipeline improves Raman baseline correction. Status: untested.
4. RMSE below any fixed threshold is blocked until data, ground truth, precision audit, reproducible script, and CI artifact exist.
5. Publication readiness is blocked until manuscript, figures, experiments, limitations, and references are complete.

## Risks

- Parameter posterior may be non-identifiable when baseline and broad peaks overlap.
- Synthetic performance may not transfer to measured spectra.
- Very low RMSE claims may reflect the benchmark setup rather than real performance.
- MCMC adds computational cost and must be justified by uncertainty value.
- Baseline correction can remove broad features if used blindly.

## Promotion gates

Add deterministic AsLS implementation, MCMC wrapper with fixed seeds, synthetic spectra with known baselines, real-data test case or documented public dataset, script-generated tables and figures, CI smoke test, and generated benchmark artifacts.

## Canonical rule

No claim moves from draft to canon without source data, executable reproduction, uncertainty accounting, and failure-case disclosure.
