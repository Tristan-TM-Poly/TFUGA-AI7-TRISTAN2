# Plus Ultra GitHub Next Actions

Date: 2026-06-27  
Status: OAK-safe execution roadmap. No destructive action, no public disclosure decision, no legal/IP decision, no external delivery.

## Objective

Convert the current GitHub ecosystem from many powerful branches into a readable, testable, mergeable, publishable, and monetizable operating system.

## Immediate merge strategy

### PR #83 — Ω-DeepTech Intelligence Forge

Recommended priority: highest.

Reason:

- small and focused;
- tied directly to IP/revenue/prototype routing;
- includes tests for unsourced claims, patent-review routing, and service-revenue routing;
- low external-action risk because it stays heuristic/draft/review-only.

Required before merge:

```text
python -m pytest tests/test_omega_deeptech_forge.py
```

Post-merge next module:

```text
prior_art_query_pack_generator.py
```

### PR #82 — Ω-GAME-T GameEngines and GameMasters

Recommended priority: high potential, but review carefully.

Reason:

- very strong conceptual/prototype layer;
- useful as sandbox for TFUGA/HGFM/CVCD/OAK;
- currently large enough to require CI or split-review discipline.

Required before merge:

```text
cd omega_game_t
python -m pytest
```

Recommended split if needed:

1. core graph primitives;
2. OAK gate;
3. memory and GM agent;
4. TextWorld engine;
5. Quest-CVCD;
6. tests and docs;
7. GameQualityScore benchmark.

## P0 — Legibility layer

- Add `MASTER_SYSTEM_INDEX.md`.
- Add `docs/canon/top40x256/README.md`.
- Add this roadmap.

These files make the ecosystem navigable before adding more systems.

## P1 — First three canonical pushes

### 1. AUTO² Kernel

Deliverables:

- CI workflow;
- one CLI demo;
- one dry-run GitHub issue generator;
- one OAK report artifact;
- one M⁻ report.

### 2. Ω-LIN-T

Deliverables:

- package-ready README;
- paper-style Markdown note;
- three example reports: pendulum, Van der Pol, Duffing;
- optional figures;
- release tag `omega-lin-v0.1` after checks.

### 3. FFWT-HAC-CVCD

Deliverables:

- FFT vs DWT vs FFWT baseline;
- noise sweep;
- ablation table;
- one real dataset adapter;
- report with M⁻ limitations.

## P2 — Revenue/IP bridge

Connect:

```text
DeepTech Forge -> Company Revenue IP Publication OS -> Value Pipeline OAKBench -> GitHub issue/draft packet
```

Minimal safe loop:

```text
signal -> evidence level -> IP class -> revenue route -> review packet -> human approval record
```

## P3 — Top40×256 crystal extraction

Create 16 cards under:

```text
docs/canon/top40x256/cards/top16/
```

Each card must be DCT-Ω compliant and include at least one minimal test or reason why it remains in quarantine.

## P4 — Repository split hygiene

Long-term target:

```text
tfuga-canon-private
tristan2-runtime-private
ai7-execution-private
fractal-loop-pilots-private
research-thesis-private
energy-core-private
```

Until then, keep this repo as the public/preview nucleus and move sensitive IP or unpublished invention details behind private review gates.

## Red locks

Do not automate these without explicit human approval and audit record:

- merge massive PRs without tests;
- publish invention details;
- send external emails/outreach;
- spend money;
- change repo permissions;
- delete files;
- claim physical/scientific certification from scaffold code;
- claim patentability or legal status.

## Working law

```text
Make the best things smaller, tested, linked, and useful before making them larger.
```
