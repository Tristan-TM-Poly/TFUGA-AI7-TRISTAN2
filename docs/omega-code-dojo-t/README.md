# Ω-CODE-DOJO-T R0.1

Ω-CODE-DOJO-T is a small OAK-safe algorithmic training laboratory for the
TFUGA-AI7-TRISTAN2 repository. It turns programming exercises into deterministic
software fixtures that can be evaluated, mutated, falsified and remembered.

## What R0.1 contains

- four original local tasks covering arrays, stacks, compression and graphs;
- seventeen deterministic cases;
- reference solvers and deliberately incorrect mutant solvers;
- an evaluator that records wrong answers and exceptions;
- an M⁻ ledger that aggregates recurring failure signatures;
- a deterministic OAK benchmark and JSON CLI;
- an optional metadata-only adapter for the public Codewars API v1;
- Python 3.10–3.13 CI.

## Commands

```bash
python -m omega_code_dojo_t.cli catalog
python -m omega_code_dojo_t.cli benchmark
python -m omega_code_dojo_t.cli benchmark --output report.json
pytest -q tests/test_omega_code_dojo_t.py
```

After installation through this repository's `pyproject.toml`:

```bash
omega-code-dojo benchmark --output report.json
```

## Codewars boundary

The adapter reads only public profile and completed-challenge metadata through
Codewars API v1. R0.1 does **not** scrape pages, copy community solutions,
extract hidden tests, automate submissions, bypass access controls or claim an
official Codewars affiliation.

The training curriculum in this module is original and local. Future adapters
must retain provenance, license and source fields and must default to metadata
rather than copied challenge bodies or solutions.

## OAK contract

A benchmark is certified only when every reference solver passes and every
included mutant is rejected. Certification means only that the finite software
fixtures behaved as specified. It does not establish general solver quality,
neural-model training, security, optimality or equivalence to Codewars ranks.

## Next versions

R0.2 can add property-based generators, subprocess isolation, resource budgets,
per-language runners, curriculum graphs and user-authorized progress snapshots.
A later learning agent can consume these reports as feedback, while keeping
training, evaluation and external-platform interaction as distinct layers.
