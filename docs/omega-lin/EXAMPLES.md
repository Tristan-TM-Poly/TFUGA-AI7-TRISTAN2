# Omega-LIN-T Examples

## Pendulum

```bash
python scripts/omega_lin_oakbench.py \
  --system pendulum \
  --output reports/omega-lin/pendulum.json \
  --markdown-output reports/omega-lin/pendulum.md
```

Expected interpretation:

- local small-angle tangent model;
- stable 2D damped system when damping is positive;
- controllable with torque-like input;
- not a global pendulum proof.

## Van der Pol

```bash
python scripts/omega_lin_oakbench.py \
  --system vanderpol \
  --output reports/omega-lin/vanderpol.json \
  --markdown-output reports/omega-lin/vanderpol.md
```

Expected interpretation:

- tangent dynamics around a non-equilibrium point;
- affine offset must be preserved;
- global limit-cycle geometry is not captured by one local model.

## Duffing

```bash
python scripts/omega_lin_oakbench.py \
  --system duffing \
  --output reports/omega-lin/duffing.json \
  --markdown-output reports/omega-lin/duffing.md
```

Expected interpretation:

- local tangent stiffness around one point;
- cubic stiffness and multi-well geometry are lost away from the local domain;
- use atlas/multi-cell linearization before extrapolating.

## Custom config

```bash
python scripts/omega_lin_oakbench.py \
  --input path/to/config.json \
  --output reports/omega-lin/custom.json \
  --markdown-output reports/omega-lin/custom.md
```

Minimal config shape:

```json
{
  "system_id": "custom_pendulum",
  "model": "pendulum",
  "parameters": {"g": 9.81, "length": 1.0, "damping": 0.05},
  "linearization": {
    "x0": [0.0, 0.0],
    "u0": [0.0],
    "state_scales": [1.0, 10.0],
    "max_radius": 1.2
  }
}
```
