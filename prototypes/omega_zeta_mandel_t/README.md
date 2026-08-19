# Ω-ZETA-MANDEL-T prototype

Dependency-free seed prototype for the Zêta-Mandelbrot-Tristan laboratory.

## What is included

- Classical Mandelbrot escape kernel with CVCD-style invariants.
- Exploratory Riemann zeta orbit kernel using the Dirichlet eta relation.
- Generic Cayley-Dickson multiplication up to sedenions.
- Sedenion Mandelbrot slice kernel with explicit OAK metadata.
- Crude zero-divisor risk probe.
- Pytest smoke tests.

## OAK guardrail

This is numerical exploration only. It must not be presented as a proof of the Riemann hypothesis or as a certified mathematical theorem.

## Run

From this folder:

```bash
python omega_zeta_mandel.py
```

Run tests from this folder:

```bash
python -m pytest -q
```

## Next implementation layers

1. Add grid renderers for Mandelbrot-CVCD and Mandelbrot-Zêta.
2. Add Newton basins for zeta zeros with validated high-precision backend.
3. Add parenthesization audits for octonion/sedenion dynamics.
4. Add OAK report generator with `visualization | heuristic | conjecture | numerical evidence | theorem` status.
5. Add M⁻ registry for false motifs caused by projection, precision, zero divisors, or color maps.
