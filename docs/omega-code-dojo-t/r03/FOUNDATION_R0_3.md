# Ω-CODE-DOJO-T∞ R0.3 — Learning Intelligence

## Status

R0.3 is a deterministic software-research layer that analyzes finite campaign receipts produced by Ω-CODE-DOJO-T∞. It does not train neural weights and does not claim pedagogical optimality, causal transfer, formal program correctness, or scientific validation.

## Research question

R0.1 asked whether a local kata-like laboratory could test reference solutions and deliberate mutants.

R0.2 asked whether the laboratory could address a combinatorial frontier without materializing billions of files, while preserving provenance and OAK limits.

R0.3 asks: **what did the system actually learn, how uncertain is that claim, which error is most informative, and what experiment should happen next?**

## Core loop

```text
campaign receipts
  -> normalized observations
  -> skill posteriors
  -> failure clusters
  -> mutation-test gaps
  -> transfer hypotheses
  -> plateau classification
  -> ranked insights
  -> finite falsifiable action plan
  -> chained learning ledger
```

## Learning is not pass count

The primary metrics are:

- information gain per cost unit;
- recurrence and reproducibility of counterexamples;
- mutation survivors, interpreted as test weakness;
- skill mastery with explicit posterior uncertainty;
- evidence-supported but non-causal transfer edges;
- novelty, information, efficiency and mastery plateaus;
- falsifier and next experiment attached to every insight.

## OAK distinctions

| Object | Meaning |
|---|---|
| Success | One observation passed its encoded fixture |
| Mastery posterior | Empirical estimate with uncertainty |
| Counterexample cluster | Recurrent failure signature |
| Test gap | Mutation score below one |
| Transfer edge | Co-evidence, not causal proof |
| Plateau | Windowed diagnostic, not permanent incapacity |
| Insight | Ranked hypothesis with falsifier |
| Learning action | Finite experiment with success and stop conditions |
| Ledger | Tamper-evident chain, not semantic truth |

## Commands

```bash
omega-code-dojo-r03 benchmark --output r03.json

omega-code-dojo-r03 analyze \
  campaign-a.json campaign-b.json \
  --plateau-window 8 \
  --output learning-report.json

omega-code-dojo-r03 plan \
  campaign-a.json campaign-b.json \
  --limit 12 \
  --output next-actions.json
```

## Certification boundary

`CERTIFIED_LEARNING_INTELLIGENCE_FIXTURES_R0_3` certifies only that the internal deterministic fixtures satisfy the encoded invariants. It does not certify human learning, model training, generalization, security, optimal curriculum, or causal relations.
