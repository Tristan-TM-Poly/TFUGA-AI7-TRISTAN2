# Omega GAME T — Core Split

Issue: #90  
Status: small merge units split from the larger GAME branch.

## Scope already merged

The first reviewable unit added:

- graph primitives;
- event validation;
- quality scoring;
- OAK gate;
- tests;
- CI.

## Split unit: PolyglotLanguageEngine-T

This branch adds a small OAK-safe language engine for GameMaster training.

It turns rough ideas into internal drafts for:

- clear French;
- clear English;
- teaching explanations;
- pitch drafts;
- Markdown documentation;
- JSON contracts;
- YAML plans;
- GitHub issue drafts;
- review-sensitive caution notes.

### Objects

- `LanguageQuest`
- `LanguageRun`
- `PolyglotLanguageEngine`

## Split unit: LanguageGM Rubric-T

This branch also adds an internal evaluation layer for LanguageGM training.

It scores LanguageRun outputs on:

- clarity;
- structure;
- audience fit;
- format fit;
- OAK safety;
- intent preservation;
- drift;
- hidden claims.

### Objects

- `LanguageRubricScores`
- `LanguageGMEvaluation`
- `LanguageGMRubric`

## Split unit: LanguageCurriculum-T

This branch adds a progressive curriculum layer for LanguageGM.

It organizes tracks, levels, quests, progress, XP, M+/M-, and next quest suggestions.

### Tracks

- `fr_clear`
- `en_clear`
- `teaching`
- `markdown_doc`
- `json_contract`
- `yaml_plan`
- `github_issue`
- `pitch`
- `ip_caution`

### Objects

- `CurriculumTrack`
- `CurriculumQuest`
- `CurriculumProgress`
- `LanguageCurriculum`

## Split unit: LanguageValidators-T

This branch adds lightweight structural validators for LanguageGM outputs.

It validates:

- Markdown docs;
- JSON contracts;
- YAML plans;
- GitHub issue drafts;
- generic language drafts.

### Objects

- `ValidationCheck`
- `ValidationReport`
- `LanguageValidators`

## Split unit: LanguageRepairLoop-T

This branch adds a deterministic improvement loop for LanguageGM drafts.

It turns validation failures into targeted repair steps, revalidates, and returns convergence, M+/M-, and the next action.

### Objects

- `RepairAction`
- `RepairAttempt`
- `RepairLoopResult`
- `LanguageRepairLoop`

## Split unit: LanguageDatasetForge-T

This branch adds a small internal dataset forge for LanguageGM benchmarks.

It stores quest, run, evaluation, validation, repair result, tags, score summary, M+ and M-.

### Objects

- `LanguageDatasetItem`
- `LanguageDataset`
- `LanguageDatasetForge`

## Split unit: Ω-GAME-SIM-EVO-T∞ R0.1

This split reconnects the original GAME/world idea to an executable headless laboratory without reviving the oversized PR #82.

Implemented:

- deterministic `Arena-T0` simulation;
- explicit `AgentGenome` and `ArenaConfig`;
- replay SHA-256 receipts;
- mirrored multi-seed round-robin tournaments;
- multidimensional ratings: performance, robustness, efficiency, novelty, stability;
- deterministic evolutionary selection/mutation;
- projection of replays into the already-merged `WorldGraph`;
- OAK + deterministic replay audits;
- bounded fuzzing for invariant discovery;
- one CLI for arena, tournament, evolution and fuzzing.

### Headless CLI

```bash
cd omega_game_t
PYTHONPATH=. python -m omega_game arena --seed 42 --steps 96
PYTHONPATH=. python -m omega_game tournament --seed 42 --population 8 --steps 64
PYTHONPATH=. python -m omega_game evolve --seed 42 --population 8 --generations 3 --steps 48
PYTHONPATH=. python -m omega_game fuzz --seed 42 --cases 100
```

Theory and evidence boundaries: `docs/theories/OMEGA_GAME_SIM_EVO_T_INFINITY.md`.

## Boundary

Omega GAME T is a game, simulation, and research lab. It is not a tool for manipulation, unfair automation, unsafe real-world instructions, or external certification.

Deterministic simulation is a reproducibility property, not evidence that a simulated law is physically true. Tournament performance is benchmark evidence, not a claim of general intelligence.

## Local test

```bash
cd omega_game_t
python -m pytest
```

## Next split units

1. sparse/event-driven scheduler + Temporal LOD;
2. quality-diversity archive / MAP-Elites;
3. Hall of Fame and M- counterexample memory;
4. agent ↔ map coevolution;
5. adversarial level generation and hidden challenge seeds;
6. GameSpec compiler;
7. TextWorld / Quest-CVCD adapters;
8. profiler-driven CPU/GPU scheduling experiments.
