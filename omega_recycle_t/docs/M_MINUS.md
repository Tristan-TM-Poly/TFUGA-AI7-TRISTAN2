# M⁻ — Ω-RECYCLE-T∞ R0.1

Negative memory is part of the model, not cleanup.

## Known limitations

| ID | Failure / limitation | Consequence | Required repair |
|---|---|---|---|
| M-001 | Components optimize independently | Cannot represent shared plant capacity or transport coupling | Add constrained global optimizer |
| M-002 | Synthetic benchmark economics | Scores are not market valuations | Add dated, provenance-tracked input datasets |
| M-003 | Mixture entropy is only a descriptor | Can be mistaken for complete thermodynamic separation cost | Keep claim boundary and add exergy/process models |
| M-004 | Functional probability is supplied | Bad inspection estimates can change chosen route | Add Bayesian uncertainty and sensitivity bands |
| M-005 | Preservation hierarchy is a prior | It can bias against a lower-level route that is actually better | Keep weight explicit and benchmark ablations |
| M-006 | No lifecycle assessment engine | Environmental superiority cannot be inferred | Integrate standard LCA inventories before claims |
| M-007 | Hazardous routes are simulation-only | Prototype cannot authorize real battery/chemical handling | Preserve certified-process gate |

## Anti-overclaim rule

A higher `score` means only “higher under the declared model and weights.” It is not proof of sustainability, profitability, safety or regulatory compliance.
