# Ω-MAIL-GITHUB-LOOP-T R0.1

A bounded, convergent mail-to-GitHub development system.

## Core loop

```text
MAIL -> COMMAND -> CASE -> ISSUE -> BRANCH -> CHANGE -> TEST -> OAK -> DRAFT PR -> MAIL REPORT
```

## Boundary

Email is untrusted input. It can request work and narrow a pre-existing policy, but it cannot grant itself repository authority. The package never authorizes automatic merge, release, force-push, repository deletion, public disclosure, secret publication, or direct writes to the default branch.

## Components

- typed loop cases, authority levels and states;
- `OMEGA-GITHUB:` command-block parser;
- duplicate and auto-reply suppression;
- deterministic case, issue, branch, PR and reply planning;
- bounded authority checks;
- measurable convergence score;
- adaptive cost budget and no-gain stop rules;
- repeated-failure M-minus stop;
- append-only evidence hash chain;
- deterministic 147,456-cell policy atlas.

## Command block

```yaml
OMEGA-GITHUB:
repo: Tristan-TM-Poly/TFUGA-AI7-TRISTAN2
action: improve
target: omega_inbox_outcome_t/intent.py
objective: Reduce false-positive intent classifications
required:
  - add lexical boundaries
  - add regression tests
authority:
  create_issue: yes
  create_branch: yes
  commit: yes
  open_draft_pr: yes
  merge: no
base_branch: main
```

## Separation of authorizations

The runtime and the GitHub operator must treat these as separate actions:

1. create or update an issue;
2. create a feature branch;
3. commit bounded files;
4. open or update a draft PR;
5. mark ready for review;
6. merge;
7. release.

A mail command is not sufficient authorization for steps 5-7.

## Convergence

An iteration continues only when it produces measurable gain and remains inside the adaptive cost/risk budget. It stops on acceptance, repeated no-gain, repeated failure, exhausted budget, missing information, OAK block or human stop.

## Atlas

```text
16 intents x 16 target families x 8 risk modes x 6 authority levels
x 4 action classes x 3 layers = 147,456 cells
```

The atlas is generated as a CI artifact rather than committed as bulk noise.
