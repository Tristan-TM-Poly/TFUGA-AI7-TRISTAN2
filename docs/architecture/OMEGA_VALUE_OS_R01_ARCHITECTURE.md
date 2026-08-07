# Ω-VALUE-OS-T∞ R0.1 — Architecture

## Data flow

```text
ValueCase
  -> schema/semantic validation
  -> constitutional hard gates
  -> claim ceiling
  -> context profile
  -> geometric soft court
  -> debt penalty
  -> evidence/closure/reuse factors
  -> abstain / experiment / human-review routing
  -> portfolio Pareto + opportunity cost
  -> deterministic DecisionReport + SHA-256
```

## Package

| File | Responsibility |
|---|---|
| `models.py` | typed enums, ValueCase, DecisionReport, canonical digests |
| `constitution.py` | seven articles, seven kernels, context profiles |
| `scoring.py` | geometric court, debts, claim ceiling, Pareto, opportunity cost |
| `engine.py` | non-compensatory judiciary and portfolio routing |
| `fixtures.py` | deterministic positive/adversarial fixtures |
| `cli.py` | read/evaluate/report-only CLI |
| `__main__.py` | `python -m omega_value_os_t` entrypoint |

## Trust boundary

The package is a pure evaluator. It does not:

- call GitHub;
- execute subprocesses;
- access the network;
- mutate repositories;
- publish artifacts;
- spend money;
- file IP;
- contact people;
- operate physical systems.

All remote authority remains outside the package.

## Non-compensatory court

The following are hard blockers:

```text
integrity
safety
legality
consent
critical_provenance
claim_ceiling violation
A4/A5 without explicit human approval
A3 with reversibility < 0.50
```

Soft dimensions are only evaluated after these conditions are represented. A blocked case retains diagnostics but receives `effective_value = 0` for the proposed action.

## Context profiles

Profiles are immutable R0.1 policy objects. They change weights and evidence floors without changing the value ontology. Adding a new profile requires tests showing that it does not relax hard gates.

## Determinism

- canonical sorted JSON;
- SHA-256 input and report IDs;
- sorted gate failures and warnings;
- sorted portfolio reports;
- deterministic Pareto output;
- no wall-clock timestamp in core receipts.

Temporal evidence will be added in R0.2 with explicit version/time semantics rather than hidden nondeterminism.

## Failure semantics

Invalid inputs fail closed with `ValueError` / CLI exit code 2. Missing hard gates, unknown dimensions, unknown debt types, non-finite numbers, out-of-range scores and non-zero claims without assumptions are rejected rather than repaired.

## Extension law

Every extension must preserve:

1. hard gates are non-compensatory;
2. score != probability;
3. claim strength cannot silently outrun evidence;
4. abstention remains possible;
5. external evidence cannot override safety/legal/consent gates;
6. all action authority remains explicitly bounded;
7. fixtures include at least one negative/adversarial case;
8. outputs remain deterministic for identical inputs;
9. new metrics document units and semantics;
10. scientific, legal, safety, IP and market claims remain scoped to their actual evidence.
