# M⁻ — Ω-RECYCLE-T∞ R0.3

Negative memory is part of the model, not cleanup.

| ID | Failure / limitation | R0.3 state | Required next repair |
|---|---|---|---|
| M-001 | Coupled optimization can explode combinatorially | Partially repaired: exhaustive oracle + branch-and-bound; worst case remains exponential | Add scalable network/capacity formulation and performance curves |
| M-002 | Synthetic benchmark economics | Open | Add dated provenance-tracked public/partner datasets |
| M-003 | Mixture entropy is only a descriptor | Open | Add process/exergy models before thermodynamic claims |
| M-004 | Functional probability was supplied as a point estimate | Partially repaired: Beta posterior propagation | Calibrate posterior from inspection/history and score calibration |
| M-005 | Preservation hierarchy can bias route choice | Partially repaired: explicit mass/value/no-preservation baselines | Run ablations on empirical datasets |
| M-006 | No lifecycle assessment engine | Partially repaired: inventory-only interface | Add recognized LCIA characterization with explicit system boundaries |
| M-007 | Hazardous routes require professional handling | Intentionally open | Preserve simulation-only/certified-process gate |
| M-008 | Finite B&B budget can stop before optimum | Explicitly represented | Track incumbent/bound gap and benchmark node budgets |
| M-009 | Monte Carlo posterior summaries depend on draws/seed | Explicitly represented | Add convergence diagnostics and analytic thresholds where possible |
| M-010 | Electronics/Battery/Building adapters are schemas, not measurements | Open | Connect versioned empirical datasets with provenance |
| M-011 | Industrial symbiosis matcher is greedy | Open | Add exact small-instance matcher and regret benchmark |

## Anti-overclaim rule

A higher `score` means only “higher under the declared model and weights.” A solver certificate means only that the declared discrete optimization problem was completed. Neither is proof of sustainability, profitability, safety, regulatory compliance or real-world superiority.
