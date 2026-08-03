# Ω-MILLENNIUM-T∞ R0.1

## Status

Research-software architecture and deterministic fixtures only.

This package does **not** claim to solve Riemann, P versus NP, Navier–Stokes,
Yang–Mills, Hodge or Birch–Swinnerton-Dyer. Poincaré is represented only as a
solved positive-control benchmark for dependency reconstruction.

## Mother invariant

A candidate proof is represented as a finite hyperpath from declared axioms,
definitions and known results to a target claim. Every hyperedge records all
premises, the conclusion, its evidence and its OAK level.

The software asks:

1. Is the statement well typed?
2. Which dependencies are explicit?
3. Which exact lemma frontier blocks the target?
4. Can a finite adversarial harness refute a candidate lemma?
5. Are both directions of a claimed equivalence present?
6. Does the available evidence permit the requested OAK level?
7. Can a conservative formal skeleton expose hidden obligations?

## R0.1 engines

- `registry.py`: seven exact program entries and anti-shortcut barriers;
- `graph.py`: multi-premise proof edges, reachability, local frontier and digest;
- `oak.py`: evidence/dependency promotion gate;
- `adversary.py`: finite Cartesian and boundary-case counterexample search;
- `equivalence.py`: two-direction equivalence audit;
- `strategy.py`: Bayes-Tristan-inspired effort routing, not truth probability;
- `formal_bridge.py`: Lean 4 skeletons containing explicit unresolved `sorry`;
- `receipts.py`: deterministic SHA-256 research event chains;
- `campaign.py`: finite resource allocation with no permanent total cap;
- `benchmark.py`: Poincaré dependency fixture and toy adversarial controls.

## Evidence ladder

| Level | Meaning |
|---:|---|
| 0 | intuition |
| 1 | well-typed statement |
| 2 | sourced/known cases |
| 3 | finite numerical or symbolic testing |
| 4 | proof in a declared restricted model |
| 5 | complete general manuscript candidate |
| 6 | proof-assistant certificate |
| 7 | independent review evidence |

A computation is capped at OAK-3. A solution claim cannot reach OAK-6 without
formal-proof evidence and cannot reach OAK-7 without independent review.

## Commands

```bash
omega-millennium registry
omega-millennium graph-demo
omega-millennium benchmark
omega-millennium campaign --budget 100
omega-millennium formal-demo
```

## R0.2 frontier

1. ingest theorem metadata with provenance and version pinning;
2. represent quantified signatures rather than free-form statements;
3. add SAT/SMT and computer algebra adapters behind explicit trust boundaries;
4. generate Lean/Isabelle/Coq declarations from typed intermediate forms;
5. build problem-specific laboratories for critical scaling, spectral
   positivity, circuit barriers, gauge-invariant continuum limits,
   cycle-class maps and analytic/arithmetic rank comparison;
6. reconstruct a deeper accepted Poincaré dependency subgraph as a positive
   control;
7. score novelty only after literature and prior-result deduplication.

## M⁻ anti-error memory

- finite verification is not universal proof;
- a new notation is not a new lemma;
- one implication is not an equivalence;
- a restricted-model theorem is not a general theorem;
- a formal skeleton containing `sorry` is not a certificate;
- a high strategy score is not probability of truth;
- a software test is not mathematical peer review;
- no agent may be sole author, adversary and final certifier of the same claim.
