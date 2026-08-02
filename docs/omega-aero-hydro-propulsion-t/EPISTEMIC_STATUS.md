# Ω-AERO-HYDRO-PROPULSION-T∞ — Epistemic and safety boundary

## What R0.1 establishes

R0.1 establishes that the repository can represent rotor geometry, calculate a deterministic low-order blade-element estimate, screen cavitation and tip Mach, search a finite design grid and reproduce its computational gates.

## What it does not establish

It does not certify or prove:

- safe flight or seaworthiness;
- engine, propeller, rotor, fan, pump or turbine performance in service;
- structural integrity, fatigue life, containment or bird-strike tolerance;
- flutter, vibration, noise or thermal margins;
- combustion stability or emissions;
- cavitation-free operation from a resolved pressure field;
- superiority over established industrial tools;
- compliance with Transport Canada, FAA, EASA, class-society or other standards.

## Mandatory promotion path

```text
LOW_ORDER_SCREENING
→ validated sectional data
→ higher-fidelity CFD/free-wake model
→ mesh/time-step convergence
→ structural and thermal coupling
→ uncertainty and off-design envelope
→ wind-tunnel/water-tunnel or bench measurement
→ independent review
→ applicable regulatory certification
```

Generated designs remain candidates. No output should be used directly to manufacture or operate a safety-critical rotor without qualified engineering review and validation.
