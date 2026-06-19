# Bayes-Tristan Scoring for GitHub Reactor — 2026-06-19

Status: OAK-safe decision layer  
Root PR: #36

## 1. Purpose

The GitHub Reactor now has a local scoring layer that ranks next actions from:

- propagation queue;
- claims registry;
- M_MINUS memory;
- atlas validation report;
- claims validation report.

The scorer does not create issues, branches, PRs, network calls, releases or external side effects.

## 2. Formula

```text
score = information_gain + cvcd_gain + prototype_value - cost - risk - m_minus_penalty
```

## 3. Interpretation

| Component | Meaning |
|---|---|
| `information_gain` | How much this action clarifies the repo ecosystem |
| `cvcd_gain` | How much it compresses/coheres the ecosystem into reusable canon |
| `prototype_value` | How much executable/testable capability it creates |
| `cost` | Expected implementation burden |
| `risk` | Chance of noisy, ambiguous, or premature promotion |
| `m_minus_penalty` | Penalty from known failures, open residues, or validation errors |

## 4. Outputs

```text
reports/github-autonomous-reactor/bayes_tristan_action_scores.json
reports/github-autonomous-reactor/BAYES_TRISTAN_ACTION_SCORES.md
```

## 5. Why this matters

The old question was:

```text
What should I do next?
```

The new question is:

```text
Which next action maximizes evidence, coherence and prototype value while minimizing cost, risk and known failure patterns?
```

## 6. OAK boundary

A high Bayes-Tristan action score is a recommendation for attention, not permission to merge or promote canon.

```text
score recommends -> tests evaluate -> review decides -> OAK promotes
```

## 7. Canonical loop

```text
claims + atlas + M_MINUS + propagation_queue
  -> Bayes-Tristan scorer
  -> ranked_actions
  -> draft PR / issue proposal
  -> workflow artifacts
  -> review
  -> canon or repair
```

## 8. Plus Ultra target

The long-term target is a repository system where every repo can answer:

```text
What is my highest-value next action?
Why that action?
What evidence supports it?
What failures penalize it?
What artifact proves it ran?
What review gate remains?
```
