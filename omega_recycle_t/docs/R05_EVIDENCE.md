# Ω-RECYCLE-T∞ R0.5 — Evidence Court

R0.5 is a software/evidence-contract increment. It does not claim industrial or environmental superiority.

## Executable courts

The deterministic `python -m omega_recycle evidence-r05` report exercises:

- Eurostat TSV dimensions, periods, `KG_HAB` normalization and a retained `p` status flag;
- EPA SMM normalized bridge plus explicit US-short-ton to metric-tonne conversion;
- normalized snapshot revision detection with modified and added records;
- a deliberately deteriorating temporal probability sequence;
- a negative-control prediction campaign where the baseline beats the canonical Ω method;
- a directed source -> hub -> sink multi-hop flow with exact finite optimum;
- a time-expanded source@0 -> hub@0 -> holdover -> hub@1 -> sink@1 flow.

These are regression/schema fixtures, not live downloaded empirical observations.

## Compatibility court

R0.5 preserves the previous `oakbench` entry point and the R0.3/R0.4 contracts: exhaustive-vs-branch-and-bound cross-check, greedy-vs-exact symbiosis counterexample, bipartite transport optimum, provenance-hash reproducibility and explicit non-certified LCIA boundary.

## CI contract

The dedicated `omega-recycle-ci` matrix runs CPython 3.11, 3.12 and 3.13. Each job installs the package, compiles the package, runs the complete tests, replays R0.3/R0.4 OAKBench courts, and replays all R0.5 evidence courts.

The R0.5 code head `3c67f932a17a9c93eb72bbd93aa018e56679fa17` passed the complete dedicated matrix and Ω Actions ΔCI before this documentation promotion.

## Source contract rationale

Eurostat is modeled as a structured TSV/SDMX-style source whose dimensions, units, time periods and observation flags must survive ingestion. R0.5 therefore preserves raw codes while exposing a tiny explicit unit map for the forms already required by the recycling use case.

EPA is deliberately more conservative: R0.5 accepts a normalized bridge table with explicit columns rather than claiming a universal parser for changing HTML, spreadsheets or PDFs. Upstream extraction therefore remains versioned, inspectable work.

## Falsification / M⁻ rules

- A valid upstream row that is silently misparsed is a parser failure.
- A source schema/unit revision that is silently accepted as equivalent is a revision-gate failure.
- A real baseline that beats Ω remains a result, not a tuning target to erase.
- A flow instance that disagrees with an independent solver blocks promotion of the optimizer certificate.
- Separate single-commodity solves must not be presented as shared-capacity multi-commodity optimization.

## Next empirical court

R0.6 should acquire immutable public snapshots with source URL, retrieval metadata, upstream version/update evidence and canonical hashes, then run cross-source/unit validation, real baseline regret, temporal calibration and independent optimization-solver comparisons.
