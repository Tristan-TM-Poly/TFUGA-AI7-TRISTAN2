# Omega-LIN-T v0.1 Release Checklist

Target tag: `omega-lin-v0.1`

## Required before tag

- [ ] `python -m pytest tests/test_omega_lin_oakbench.py` passes.
- [ ] `omega-lin-ci` passes on PR.
- [ ] JSON reports generated for pendulum, Van der Pol, and Duffing.
- [ ] Markdown reports generated for pendulum, Van der Pol, and Duffing.
- [ ] README explains OAK boundary.
- [ ] Paper note distinguishes local model from global nonlinear solution.
- [ ] M-minus limitations are explicit.
- [ ] No safety-critical control certification claim.
- [ ] No revenue claim.
- [ ] No patentability or legal claim.

## Acceptance commands

```bash
python scripts/omega_lin_oakbench.py --system pendulum --output reports/omega-lin/pendulum.json --markdown-output reports/omega-lin/pendulum.md
python scripts/omega_lin_oakbench.py --system vanderpol --output reports/omega-lin/vanderpol.json --markdown-output reports/omega-lin/vanderpol.md
python scripts/omega_lin_oakbench.py --system duffing --output reports/omega-lin/duffing.json --markdown-output reports/omega-lin/duffing.md
python -m pytest tests/test_omega_lin_oakbench.py
```

## Release note seed

Omega-LIN-T v0.1 provides a stdlib-only local linearization OAKBench for pendulum, Van der Pol, and Duffing examples, including residuals, validity radius, curvature, stability/controllability checks, invariant audit, and M-minus warnings.

## OAK boundary

Research/education prototype only. Not a global nonlinear solver, not a physical controller, and not a safety certification.
