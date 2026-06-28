# GitHub Autonomous Reactor Analysis — 2026-06-19

Status: OAK-safe operational analysis packet  
Scope: connected GitHub account `Tristan-TM-Poly` and the six accessible repositories observed through the GitHub connector.  
Mode: zero-touch where possible, but no unsafe force-push, no direct main rewrite, no autonomous merge.

## 1. Repository inventory

| Repository | Visibility | Size signal | Role hypothesis | Current action class |
|---|---:|---:|---|---|
| `Tristan-TM-Poly/PEFA-FractalEnergySystem` | private | small | PEFA / fractal energy research scaffold | needs executable simulation + conservation tests |
| `Tristan-TM-Poly/Tristan_Tardif-Morency_TFUG` | public | very large | legacy/main corpus, TFUG archive, audit tools, hyperatlas | needs extraction, indexing, CI hygiene, canon registry |
| `Tristan-TM-Poly/Tristan_Tardif-Morency_TFUGAG` | public | small/medium | AIT generator / TFUGAG package layer | needs package tests + release path |
| `Tristan-TM-Poly/TFACC` | private | medium | converted/canon corpus and reports | needs classification + reproducibility checks |
| `Tristan-TM-Poly/TFUGA-AI7-TRISTAN2` | public | medium-large | current root reactor: TFUGA / AI-7 / SAGE / AIT canon | primary automation nucleus |
| `Tristan-TM-Poly/TTM-TFUGA-AI7-TRISTAN2` | public | small | mirror/variant seed | needs role clarification and sync policy |

## 2. Current strongest assets found

### 2.1 Guarded autonomy already exists

The root repo contains an `Autopilot Tools` layer with safe local/home-server policy:

```text
scan -> report -> branch -> draft PR -> checks -> human/canonical promotion
```

This is the correct pattern. It preserves autonomy without allowing uncontrolled self-modification.

### 2.2 OAK/CVCD report generator exists

`tools/autopilot/oak_cvcd_report.py` is a standard-library scanner that:

- reads repository files;
- writes `reports/autopilot/autonomous_build_report.json`;
- writes `reports/autopilot/autonomous_build_report.md`;
- writes `reports/autopilot/m_minus_latest.json`;
- does not execute shell commands;
- does not open network connections.

This is a strong root primitive for all future autonomous propagation.

### 2.3 Auto-genesis kernel exists

`core/genesis_kernel.py` already encodes the right guardrail:

- read theory/prototype corpus;
- run OAK benchmark prototype when available;
- produce CANON / FERTILE / M_MINUS registry;
- produce report and improvement queue;
- never rewrite source code autonomously;
- only write reports under `reports/auto_genesis/`.

It also produces an explicit improvement queue including:

- freeze CANON benchmarks as regression tests;
- investigate M_MINUS findings;
- replace analytic surrogate with a true adaptive FFWT core;
- add FFT/STFT/DWT/CWT/PCA/SVD baselines;
- add R/C/H/O/S16 algebra ablation matrix.

### 2.4 Continuous audit exists in the large TFUG corpus

`tools/ai7_audit/continuous_audit.py` in `Tristan_Tardif-Morency_TFUG` already performs bounded checks:

- repository inventory;
- Python syntax compilation;
- optional unit test discovery summary;
- AntiHype scan for unsupported high-risk claims;
- synthetic curve-fit smoke test;
- hypergraph proxy from path/component co-occurrence;
- DCT++ truth-level summary.

This should be promoted into the shared audit standard across repositories.

### 2.5 Open PR ecosystem already contains the right building blocks

The open PR stream shows a mature direction:

- repo canon role PRs across repositories;
- canon unification scaffold;
- interrepo HGFM atlas;
- home-server autonomous builder layer;
- open-source data automation manager;
- AIT GitHub/cloud/server managers;
- Tristan Omni Core shared kernel;
- HGFM canon and OAK-strict theory packages.

## 3. Diagnosis

### 3.1 Main problem

The ecosystem already has many powerful modules, but they are distributed across several repos and PRs.

The immediate bottleneck is not idea generation. It is:

```text
unified reactor discipline + CI consistency + claim registry + safe propagation rules
```

### 3.2 Current highest-value root repository

`TFUGA-AI7-TRISTAN2` should act as the root reactor because it already has:

- auto-genesis workflow;
- autopilot tools;
- home-server plan;
- current canon PRs;
- interrepo atlas material;
- root OAK/CVCD language.

### 3.3 Current highest-value legacy repository

`Tristan_Tardif-Morency_TFUG` should act as the deep corpus mine because it has:

- very large corpus size;
- AI-7 continuous audit;
- u0_core minimal generator;
- institutional hyperatlas validation;
- notebooks and imported materials.

### 3.4 Current highest-risk branch

Energy/physics repositories and claims need strict OAK gates.

For `PEFA-FractalEnergySystem`, the README already correctly marks the repository as a research scaffold until equations, simulations, tests, and prototype logs are added. The next valid move is not stronger claims; it is executable conservation/stability tests.

## 4. Proposed reactor architecture

```text
GITHUB AUTONOMOUS REACTOR

Layer 0 — Repository inventory
  list repos, branches, PRs, files, workflows, package manifests

Layer 1 — Static safety audit
  compile Python, validate schemas, detect high-risk overclaims, detect missing tests

Layer 2 — OAK/CVCD report
  classify CANON / FERTILE / M_MINUS / REPAIR / ARCHIVE

Layer 3 — Build matrix
  run pytest if tests exist; otherwise syntax compile and smoke tests

Layer 4 — Propagation planner
  generate suggested branch/PR packets, never direct main rewrites

Layer 5 — Draft PR construction
  create additive files only; open draft PR; never force-push; never auto-merge

Layer 6 — Canon promotion
  only after tests, review, OAK gates, low residue, and M_MINUS accounting
```

## 5. Safe push/update policy

Allowed automatically:

- generate reports;
- update audit artifacts;
- create additive docs/schemas/manifests;
- create branches;
- open draft PRs;
- upload artifacts;
- label findings as CANON/FERTILE/M_MINUS/REPAIR;
- propose next actions.

Not allowed automatically:

- force-push;
- merge to main;
- delete user files;
- rewrite source code without review;
- make physical/financial/legal/official claims;
- deploy to external infrastructure with secrets;
- contact institutions;
- publish outside GitHub;
- claim validation without measurement/proof.

## 6. Canonical propagation loop

```text
repo scan
  -> OAK/CVCD report
  -> M_MINUS update
  -> build/test matrix
  -> generated improvement queue
  -> branch packet
  -> draft PR
  -> checks
  -> review/canon decision
```

## 7. Priority queue

### P0 — Merge/resolve root canon PRs

1. Review PR #35 `Canon unification scaffold for TFUGA AI7 AIT`.
2. Review PR #34 `[codex] Add repo canon role`.
3. Review PR #21 `Add Tristan Hypergraphs HGFM OAK-strict canon`.
4. Keep the root canon additive until registry/schema checks exist.

### P0 — Standardize audit across all repos

Each repo should receive:

```text
docs/REPO_CANON_ROLE.md
schemas/OAK_SCHEMA.yaml or link to root schema
reports/autopilot/README.md
.github/workflows/repo-audit.yml
```

### P1 — Build/test normalization

Each repo should expose at least one command:

```bash
python -m compileall .
pytest
python tools/autopilot/oak_cvcd_report.py --repo-root . --mode full
```

### P1 — M_MINUS registry

Create a persistent negative-memory registry in the root repo:

```text
memory/m_minus/github_m_minus_registry.jsonl
```

Each failed check should become a structured anti-pattern, not noise.

### P1 — Interrepo atlas hardening

The interrepo atlas should become machine-readable and CI-checked:

```text
atlas/repositories.yml
atlas/hyperedges.yml
atlas/propagation_rules.yml
```

### P2 — Home server runner

Home runner should only be enabled after:

- branch protection is configured;
- secrets policy is documented;
- dry-run bootstrap passes;
- jobs are restricted to labels `self-hosted, linux, x64, home-lab`;
- no secrets are printed;
- no auto-merge to main.

## 8. Bayes-Tristan ranking for next actions

| Action | Truth/proof gain | Fertility | Risk | Cost | Decision |
|---|---:|---:|---:|---:|---|
| Add repo audit workflow to root | high | high | low | low | DO NOW |
| Merge canon unification after review | medium-high | high | medium | low | REVIEW THEN MERGE |
| Create cross-repo OAK schema | high | high | low | medium | DO NEXT |
| Auto-merge everything | low | medium | high | low | FORBIDDEN |
| Add PEFA conservation tests | high | high | low-medium | medium | PRIORITY |
| Enable self-hosted runner | medium | high | medium-high | medium | AFTER GUARDRAILS |
| Push source self-modifier | low | high | high | medium | BLOCKED UNTIL PR GATES |

## 9. Recommended immediate packet

This branch should add:

1. this analysis document;
2. a machine-readable autonomous reactor manifest;
3. a non-destructive GitHub Actions audit workflow.

The result should be a draft PR, not a direct merge.

## 10. Final operating rule

```text
Autonomy is allowed to observe, measure, report, branch, and propose.
Autonomy is not allowed to silently certify, force, merge, deploy, or overclaim.
```

This is the correct foundation for your zero-touch GitHub ecosystem: maximum propagation, but OAK-gated and reviewable.
