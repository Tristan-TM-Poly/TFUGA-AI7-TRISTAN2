# Ω-SPACE-HG-T∞ R0.4 MAX — Reliability, Radiation and FDIR

## Scope

R0.4 adds a deterministic reliability laboratory above the R0.1–R0.3 mission,
dynamics and network stack. It models component failures, redundant functions,
explicit common-cause groups, simplified radiation-event counts, diagnostic
coverage, probabilistic recovery, fault trees, permission-bounded FDIR and
resumable Monte-Carlo campaigns.

All canonical rates, coverages and recovery probabilities are synthetic research
fixtures. They are not vendor data, measured predictions, safety certification
or flight qualification.

## Reliability kernel

For a constant hazard rate `λ`, the finite-exposure probability is:

```text
P(failure by t) = 1 - exp(-λ t)
```

Deterministic inverse-transform sampling maps `(seed, stream)` to a failure time.
The same campaign offset therefore reproduces the same trials and witnesses.

A function survives while at least one of its declared components remains
active or has recovered. Common-cause events can fail multiple components at
once, preventing naive redundancy from being treated as independence.

## Fault trees

`FaultTreeNode` supports:

- leaves with declared probabilities;
- `AND` gates;
- `OR` gates;
- exact independent `k-of-n` gates by finite probability convolution.

The canonical mission-loss tree covers dual flight computers, dual power
controllers and dual command radios. Its result is an independent baseline only;
common causes are evaluated separately by campaigns.

## Radiation baseline

Expected events use:

```text
N = flux × cross-section × device count × attenuation × exposure
```

Event count is sampled from a deterministic Poisson model. This does not model
particle spectra, shielding transport, deposited energy, device geometry,
single-event latchup physics, total ionizing dose or displacement damage.

## FDIR state machine

The explicit modes are:

```text
BOOT → NOMINAL → DEGRADED → RECOVERY → NOMINAL
                    ↘ SAFE ↗
                       FAILED
```

Transitions depend on detected failures, successful recovery, battery SOC,
maximum recovery attempts and unrecoverable critical failures. No generated
transition grants permission for real autonomous flight action.

## Campaign factory

`run_reliability_campaign` accepts `start_offset` and `count`, returns the exact
`next_offset`, and has no permanent total cap. Every execution is still bounded
by explicit compute and storage budgets.

Reports include:

- mission successes and failures;
- estimated success probability;
- Wilson 95% binomial interval;
- event, detection, recovery and safe-mode rates;
- retained failed trials;
- deterministic witness digest;
- explicit claim boundaries.

The confidence interval captures finite-sample uncertainty only. It does not
cover uncertainty in physical rates, dependence structure, model form, recovery
logic or environment.

## OAKBench gates

R0.4 verifies:

1. exact constant-hazard probability composition;
2. known OR-gate probability `0.28` for `p=0.1` and `p=0.2`;
3. lower canonical success when common causes are enabled;
4. linear expected-radiation-event scaling with exposure;
5. deterministic campaign replay and witness digest;
6. exact canonical FDIR mode path;
7. absence of proof, validation, qualification, operational reliability,
   certification or autonomous-safety claims.

## Commands

```bash
omega-space-hg-r04 manifest
omega-space-hg-r04 campaign --duration-days 365.25 --count 2048
omega-space-hg-r04 campaign --start-offset 1000000 --count 10000
omega-space-hg-r04 campaign --no-common-causes --no-radiation
omega-space-hg-r04 fdir
omega-space-hg-r04 oak
```

## M-minus registry

- `M⁻-SPACE-R04-001`: a constant hazard is not a complete lifetime model.
- `M⁻-SPACE-R04-002`: nominal redundancy is fragile under common causes.
- `M⁻-SPACE-R04-003`: independent fault-tree gates can understate dependence.
- `M⁻-SPACE-R04-004`: flux–cross-section Poisson counting is not radiation
  transport or device qualification.
- `M⁻-SPACE-R04-005`: diagnostic coverage and recovery probabilities must be
  measured before they support a real safety claim.
- `M⁻-SPACE-R04-006`: Monte-Carlo precision cannot repair incorrect inputs.
- `M⁻-SPACE-R04-007`: a passing FDIR fixture is not a nonlinear stability proof,
  autonomous-safety guarantee or flight-software certification.

## Next frontier

R0.5 should add constellations, sampled coverage and revisit, intersatellite
networks, distributed task allocation, graceful degradation, replenishment and
mycelial migration of functions while retaining deterministic evidence and
explicit collision/debris boundaries.
