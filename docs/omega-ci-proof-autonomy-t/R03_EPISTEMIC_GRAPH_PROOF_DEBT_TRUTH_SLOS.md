# Ω-CI-PROOF-AUTONOMY-T∞² R0.3

R0.3 adds a finite, deterministic epistemic reliability layer on top of R0.1/R0.2.

## Implemented

- typed epistemic nodes and edges for claims, assumptions, tests, evidence, counterevidence, residuals and environments;
- graph validation, stable graph identities and dependency-cycle rejection;
- conservative invalidation propagation from changed evidence, assumptions, validators, tests or environments to dependent claims;
- explicit evidence-conflict reports with hypotheses and discriminating experiments;
- proof-debt accounting for missing evidence, low coverage, missing tests, non-current evidence, missing provenance, residuals and conflicts;
- Truth SLO evaluation over current critical claims, weighted claim coverage, traceability, residuals, conflicts and proof debt;
- experiment allocation by information gain per bounded cost, with sensitive capabilities and high-risk candidates rejected;
- OAKBench proving the A3 ceiling, no remote mutation and no execution authority.

## Non-claims

R0.3 does not infer real-world causality, prove scientific truth, execute experiments, patch code, push branches, merge PRs, publish releases or authorize A4. Scores are structured planning heuristics, not probabilities of correctness.

## Commands

```bash
python -m omega_ci_proof_t.r03 graph --graph data/omega_ci_proof_t/r03-graph.json
python -m omega_ci_proof_t.r03 invalidate --graph data/omega_ci_proof_t/r03-graph.json --changed EVID-EXPIRY-FIXTURE --output out/invalidation.json
python -m omega_ci_proof_t.r03 debt --graph data/omega_ci_proof_t/r03-graph.json --state data/omega_ci_proof_t/r03-state.json --output out/debt.json
python -m omega_ci_proof_t.r03 slo --graph data/omega_ci_proof_t/r03-graph.json --state data/omega_ci_proof_t/r03-state.json --slos data/omega_ci_proof_t/r03-slos.json --output out/slo.json
python -m omega_ci_proof_t.r03 conflicts --graph data/omega_ci_proof_t/r03-graph.json --output out/conflicts.json
python -m omega_ci_proof_t.r03 experiments --candidates data/omega_ci_proof_t/r03-experiments.json --budget 1.0 --output out/experiments.json
python -m omega_ci_proof_t.r03 oak
```
