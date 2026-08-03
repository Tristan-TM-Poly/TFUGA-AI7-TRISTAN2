# OAK runbook — Ω-ZETA-MANDEL-T

## Claim status ladder

- `visualization`: image or orbit pattern only.
- `heuristic`: pattern survives at least one robustness check.
- `conjecture`: clear formal statement plus counterexample search plan.
- `numerical evidence`: reproducible computation with baselines and uncertainty.
- `theorem`: proof reviewed independently.

Default status: `visualization`.

## Required metadata

Every experiment must record:

```yaml
object: Mandelbrot-CVCD | Zeta-Orbit | Mandelbrot-Zeta | Sedenion-Mandelbrot
algebra: R | C | H | O | S
projection: explicit
norm: explicit
precision: explicit
escape_radius: explicit
iterations: explicit
parenthesization: explicit
baseline: explicit
claim_status: visualization
```

## Failure modes to log in M⁻

| False signal | Likely cause | OAK test |
|---|---|---|
| zero found | precision/truncation error | compare high precision |
| new symmetry | projection artifact | change projection |
| stable sedenion orbit | zero-divisor annihilation | compute zero-divisor risk |
| critical-line coherence | sampling bias | perturb grid and compare random baseline |
| fractal dimension stable | resolution too low | multi-resolution convergence |
| prime pattern | deterministic coloring bias | randomized prime-like controls |

## Minimal pass criteria for Phase 0

- Classical Mandelbrot inside/outside smoke tests pass.
- `zeta(2)` eta approximation is close to pi^2/6.
- Cayley-Dickson complex unit satisfies `i*i = -1`.
- Sedenion kernel returns OAK warning metadata.
- Zero-divisor probe returns finite range.
