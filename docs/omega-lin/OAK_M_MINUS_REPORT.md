# Omega-LIN-T v0.1 — OAK / M-minus Report

Issue: #87  
Status: release candidate package.

## OAK checks

| Check | Result |
|---|---|
| Local linearization only | pass |
| Residuals reported | pass |
| Scaled residuals reported | pass |
| Validity radius estimated | pass |
| Curvature warning available | pass |
| Stability/controllability marked as local | pass |
| Invariant audit included | pass |
| M-minus limitations included | pass |
| CLI examples included | pass |
| CI workflow included | pass |

## M-minus limitations

- Local tangent models do not prove global nonlinear behavior.
- A nonzero affine offset must not be dropped away from equilibrium.
- A small validity radius means the model is fragile.
- Synthetic examples do not prove industrial usefulness.
- Stability/controllability checks are local 2D checks only.
- This is not safety-critical control certification.

## Promotion decision

`omega-lin-v0.1` is eligible for release after CI passes and reports are generated for pendulum, Van der Pol, and Duffing.

## Next actions after merge

1. Generate reports under `reports/omega-lin/`.
2. Tag `omega-lin-v0.1` only after checklist completion.
3. Add plots only if they clarify residual/validity domains.
4. Build a follow-up atlas-linearization prototype.
