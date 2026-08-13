# Ω-MATH-PROOF R0.1 benchmark contract

The architecture is not considered an improvement merely because it adds graphs, agents, or new names. Every later layer must beat a simpler baseline on a measured task.

## Baselines

- **B0 lexical** — keyword / exact-title retrieval.
- **B1 embedding/RAG** — ordinary chunk retrieval without MathIR.
- **B2 LLM-only** — one-pass proof/formalization candidate with no corpus structure.
- **B3 LLM + retrieval** — retrieved text but no ProofGenome or status lattice.
- **B4 fixed tactic portfolio** — static formal tactics with equal budget.

## R0.2 metrics

| Dimension | Metric |
|---|---|
| extraction | artifact-type precision / recall on manually labelled pages |
| statement fidelity | semantic round-trip error |
| proof retrieval | top-k structural analogue hit rate |
| formalization | compile rate and kernel acceptance rate |
| falsification | valid counterexamples found per compute budget |
| proof reuse | solved targets attributable to retrieved reusable structure |
| cost | wall-clock, tokens, CPU time, memory where measurable |
| contamination | structurally near-duplicate test leakage |
| provenance | fraction of claims with resolvable SourceAnchor |
| OAK | false elevation rate between status layers |

## GO MAX objective

A candidate strategy `a` at proof state `s` is useful only insofar as its measured expected value is positive:

```text
GO(a | s) = E[verified_frontier_gain + reusable_knowledge_gain]
            / (compute_cost + human_cost + risk_cost)
```

This quantity is initially an engineering score, not a mathematical law. Its predictive value must itself be benchmarked.

## Promotion rule

A new component moves from `M?` to `M+` only when it shows reproducible gain against an appropriate baseline. Components that add complexity without measured gain move to `M-` or backlog.
