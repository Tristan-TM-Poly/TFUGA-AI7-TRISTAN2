# ARK-SP-CUBE-GAIA Protocol Checklists v0.11

Status: C+ / checklist scaffold only / not measurement / not certification.

## Purpose

Turn the v0.10 protocols into reviewable, repeatable execution gates without claiming that any experiment has already succeeded.

## Global OAK gates

- [ ] Experiment title is recorded.
- [ ] Operator/reviewer name is recorded.
- [ ] Date and location are recorded.
- [ ] Sample IDs are unique.
- [ ] No high-voltage or unsafe battery setup is used.
- [ ] Baseline/control sample exists.
- [ ] Raw CSV logs are preserved.
- [ ] Photos or notes are preserved when safe.
- [ ] Uncertainty and environmental conditions are noted.
- [ ] Claim status remains MEASURED_CANDIDATE at most until independent review.

## SP-CUBE passive delta-T checklist

- [ ] Reference aluminum sample prepared.
- [ ] Reference white/cool surface prepared.
- [ ] Reference black matte sample prepared.
- [ ] SP-CUBE candidate sample prepared.
- [ ] All samples have stable labels.
- [ ] Temperature sensor placement is consistent.
- [ ] Ambient temperature is logged.
- [ ] Sky/cloud state is logged.
- [ ] Sun/shade condition is logged.
- [ ] Measurement duration is recorded.
- [ ] Delta-T is computed against baseline.
- [ ] Result is reported as observed delta-T only, not certified cooling performance.

## Ark-M1 low-power bench checklist

- [ ] Heat source is below the selected low-power safety threshold.
- [ ] Voltage and current are recorded.
- [ ] Power is computed as P = V * I.
- [ ] Temperature is logged without SP-CUBE.
- [ ] Temperature is logged with SP-CUBE.
- [ ] Same load and timing are used for both runs.
- [ ] Thermal cutoff condition is defined.
- [ ] Result is reported as bench observation only.

## Methane MRV registry checklist

- [ ] Event ID is unique.
- [ ] Source ID is unique.
- [ ] Timestamp exists.
- [ ] Location exists or is intentionally generalized.
- [ ] Source type is declared.
- [ ] GWP factor is declared.
- [ ] Uncertainty is recorded.
- [ ] Verification status is recorded.
- [ ] Duplicate event check is performed.
- [ ] No credit/revenue claim is made from simulated records.

## Failure conditions

Any of these force OAK downgrade to BLOCKED or NEEDS_REVIEW:

- unsafe electrical setup;
- missing baseline;
- missing raw logs;
- untracked sample IDs;
- value or revenue claim from simulation;
- CO2e claim without MRV uncertainty;
- methane event without unique ID;
- public wording that implies certification.

## Output

A completed checklist can support TESTED_LOCAL or MEASURED_CANDIDATE only if raw data exists. It cannot certify the system.
