# Omega-LIN-T v0.1 — Local Linearization OAKBench

## Abstract

Omega-LIN-T is a conservative local linearization benchmark for nonlinear dynamical systems. It computes finite-difference Jacobians, affine offsets, residuals, scaled residuals, directional validity radii, curvature indices, and simple local stability/controllability checks. The goal is not to replace nonlinear simulation; the goal is to make local approximations explicit, falsifiable, and bounded.

## Core model

Given a nonlinear system:

```text
dx/dt = f(x, u)
```

near `(x0, u0)`, Omega-LIN-T estimates:

```text
A = df/dx |_(x0,u0)
B = df/du |_(x0,u0)
c = f(x0,u0) - A x0 - B u0
```

and reports the affine approximation:

```text
dx/dt ~= A x + B u + c
```

plus the perturbation form:

```text
d(delta_x)/dt ~= f0 + A delta_x + B delta_u
```

## OAK contribution

Omega-LIN-T adds an OAK layer to ordinary local linearization:

- residual measurement;
- scaled residual measurement;
- validity radius estimate;
- curvature warning;
- invariant audit;
- model-specific lost/approximated structures;
- M-minus warnings when the affine offset is nonzero or the domain is too small.

## Demonstration systems

### Pendulum

Useful for showing small-angle local validity and the loss of global periodic nonlinear geometry.

### Van der Pol oscillator

Useful for showing that a tangent model can miss global limit-cycle geometry.

### Duffing oscillator

Useful for showing that local tangent stiffness cannot represent multi-well/global nonlinear behavior.

## Failure conditions

A report must not be promoted if:

- `valid_radius <= 0`;
- residuals exceed thresholds everywhere;
- affine offset is ignored away from equilibrium;
- the result is described as a global nonlinear solution;
- the result is used as a physical control certification.

## OAK boundary

This is a research and education prototype. It does not certify controllers, prove global stability, or guarantee correctness outside the reported local domain.
