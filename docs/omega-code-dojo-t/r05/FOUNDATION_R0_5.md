# Ω-MULTI-JUDGE-DOJO-T∞ R0.5 — Policy-Gated Multi-Platform Practice

R0.5 adds a conservative multi-platform layer above Ω-CODE-DOJO-T∞ R0.4.

## Platforms

- Codewars
- Exercism
- Codeforces
- CSES
- Kattis
- Project Euler
- AtCoder
- DMOJ
- Advent of Code

The registry is an executable policy fixture, not legal advice. It defaults toward review or blocking whenever access, licensing, automation, redistribution, training, or commercial use is unclear.

## Four operating modes

```text
DISCOVER → metadata or identifiers through an allowed mechanism
PRACTICE → local work on user-authorized material
SUBMIT   → manual action unless an official interface and permission allow automation
TRAIN    → only user-owned or explicitly licensed/permitted material
```

## No content mirror

The normalizer accepts identifiers, titles, tags, difficulty, progress state, locators, and small metadata fields. It rejects statement, solution, editorial, hidden-test, private-test, and answer fields.

## Shadow problems

External references are mapped only to abstract skills. R0.5 then generates an original synthetic fixture from one of the 17 R0.4 families:

```text
external metadata reference
→ canonical skill vector
→ priority score
→ original synthetic shadow problem
→ fragile strategy
→ independent oracle
→ exact fallback
→ counterexample memory
```

A solved shadow fixture is not a solved external problem. Every receipt keeps `external_problem_solution_claimed=false` and `manual_submission_required=true`.

## Scale

The initial logical reference address space is:

```text
9 platform namespaces × 2^32 reference slots × 32 difficulty bands
= 1,236,950,581,248 addressable reference cells
```

This is a logical architecture. The benchmark discovers 593 fixture references, normalizes 585, selects 585, and materializes 256 original shadow problems.

## Priority function

The portfolio planner combines:

- measured weakness;
- uncertainty;
- novelty;
- source diversity;
- transfer potential;
- estimated cost;
- policy risk.

Blocked references remain visible in the audit but are not materialized.

## OAK boundary

R0.5 does not claim:

- affiliation with any platform;
- automated external submissions;
- copied statements, editorials, community solutions, or hidden tests;
- permission to train on platform content;
- resolution of external problems;
- general algorithm correctness from finite fixtures;
- neural-model training.

## Commands

```bash
omega-code-dojo-r05 registry
omega-code-dojo-r05 plan --per-platform 16 --limit 32
omega-code-dojo-r05 benchmark
```

## Next barrier

R0.6 should add real platform-specific metadata adapters behind explicit network and policy gates, persistent progress imports, subprocess-isolated multi-language runners, fuzzing, shrinking, differential oracles, and a human-approved submission queue.
