# Omega-LIN-T v0.1

Status: first public scientific prototype candidate.  
Scope: local linearization OAKBench for small nonlinear systems.

## Purpose

Omega-LIN-T estimates a local affine/tangent model of a nonlinear dynamical system and reports:

- Jacobians `A` and `B`;
- affine offset `c`;
- residuals and scaled residuals;
- estimated local validity radius;
- curvature warning;
- local 2D stability and controllability;
- invariant audit;
- OAK warnings and M-minus limitations.

## Supported examples

- pendulum;
- Van der Pol oscillator;
- Duffing oscillator.

## Commands

```bash
python scripts/omega_lin_oakbench.py --system pendulum --output reports/omega-lin/pendulum.json --markdown-output reports/omega-lin/pendulum.md
python scripts/omega_lin_oakbench.py --system vanderpol --output reports/omega-lin/vanderpol.json --markdown-output reports/omega-lin/vanderpol.md
python scripts/omega_lin_oakbench.py --system duffing --output reports/omega-lin/duffing.json --markdown-output reports/omega-lin/duffing.md
python -m pytest tests/test_omega_lin_oakbench.py
```

## OAK boundary

This is a local linearization, research, and education tool. It is not a global nonlinear solver guarantee and not a safety-critical control certification.

## Release target

`omega-lin-v0.1` can be tagged after CI passes and the release checklist is complete.
