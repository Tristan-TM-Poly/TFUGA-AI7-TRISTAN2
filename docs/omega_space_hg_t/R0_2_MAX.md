# Ω-SPACE-HG-T∞ R0.2 MAX — Perturbed Orbit and Attitude Laboratory

## Purpose

R0.2 extends the R0.1 mission factory with an executable dynamics layer for:

- first-order Earth `J2` gravity;
- an explicitly simplified exponential-atmosphere drag model;
- fixed-direction solar-radiation-pressure forcing;
- Cartesian ↔ Keplerian conversion;
- osculating orbital elements;
- numerical versus analytical secular RAAN drift;
- quaternion rigid-body attitude dynamics;
- principal-axis inertia;
- reaction-wheel torque and momentum limits;
- deterministic gyro and star-tracker error models;
- PD quaternion feedback;
- disturbance torque injection;
- magnetic-dipole torque geometry;
- deterministic OAK fixtures and claim boundaries.

The release is research and educational software. It is not an operational orbit
propagator, orbit-determination product, conjunction-assessment service, flight
controller, stability proof, hardware model or qualification artifact.

## Orbital dynamics

The acceleration model is

```text
a = a_two_body + a_J2 + a_drag + a_SRP
```

with a fourth-order Runge–Kutta state propagator. Each perturbation can be
activated independently. The atmospheric density law is deliberately exposed
as a low-fidelity baseline rather than hidden behind a claim of realism.

The OAK cross-check uses a 550 km, 97.6 degree inclined orbit and compares the
numerical secular right-ascension-of-ascending-node drift with first-order J2
theory. The declared software fixture tolerance is 2 percent over ten orbits.
Passing this gate does not validate the model outside that declared domain.

## Attitude dynamics

Attitude is represented by a scalar-first unit quaternion and body angular
velocity. Principal-axis Euler dynamics include gyroscopic coupling. A bounded
reaction-wheel command is generated from quaternion and rate error:

```text
command = 2 Kp q_error_vector + Kd rate_error
```

The implementation normalizes the quaternion at every integration step and
tracks:

- initial, final and maximum attitude error;
- maximum angular rate;
- torque saturation count;
- wheel momentum saturation count;
- maximum wheel momentum fraction;
- quaternion manifold error;
- explicit violations.

Synthetic gyro and star-tracker errors are deterministic functions of seed,
sample and axis. They exist to test replay, error propagation and controller
robustness; they are not calibrated sensor models.

## OAKBench gates

`omega-space-hg-r02 oak` checks:

1. numerical J2 RAAN drift against first-order analytical theory;
2. exact deterministic replay of selected perturbed-orbit metrics;
3. closed-loop attitude convergence from a 35 degree initial error;
4. quaternion norm preservation;
5. deterministic sensor replay;
6. absence of theorem, scientific-validation, flight, operational ephemeris,
   conjunction-assessment and stability-proof claims.

## Commands

```bash
omega-space-hg-r02 manifest
omega-space-hg-r02 orbit --duration-orbits 10 --step-s 20
omega-space-hg-r02 orbit --duration-orbits 3 --drag --srp
omega-space-hg-r02 attitude --duration-s 120 --step-s 0.2
omega-space-hg-r02 attitude --ideal-sensors
omega-space-hg-r02 oak
```

## Validation

```bash
python -m compileall -q omega_space_hg_t tests/test_omega_space_hg_r02.py
pytest -q tests/test_omega_space_hg_t.py tests/test_omega_space_hg_r02.py
python -m omega_space_hg_t.r02_cli oak
python examples/omega_space_hg_r02_demo.py
```

## Known limitations and M-minus assets

- `M⁻-SPACE-R02-001`: first-order J2 is not a complete gravity field.
- `M⁻-SPACE-R02-002`: an exponential density law cannot represent space weather,
  local time, composition, geomagnetic activity or real thermospheric variability.
- `M⁻-SPACE-R02-003`: fixed inertial Sun direction and caller-supplied illumination
  are architecture hooks, not validated eclipse or ephemeris models.
- `M⁻-SPACE-R02-004`: reaction wheels are represented through bounded ideal body
  torques and momentum accumulation; electrical, thermal, structural and bearing
  dynamics are absent.
- `M⁻-SPACE-R02-005`: convergence in the canonical fixture is not a general
  nonlinear stability proof.
- `M⁻-SPACE-R02-006`: deterministic synthetic errors support reproducibility but
  do not establish statistical calibration.
- `M⁻-SPACE-R02-007`: no generated result is suitable for operational navigation,
  collision avoidance, crew safety or flight-critical decisions.

## Next R0.3 frontier

The next depth layer should add a multinode thermal network, battery equivalent
circuit, illumination geometry, station visibility, link budgets, packet queues,
contact scheduling and CCSDS/XTCE-compatible data interfaces while retaining the
same proof-carrying hypergraph and OAK claim discipline.
