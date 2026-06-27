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

## Boundary

Omega GAME T is a game, simulation, and research lab. It is not a tool for manipulation, unfair automation, unsafe real-world instructions, or external certification.

## Local test

```bash
cd omega_game_t
python -m pytest
```

## Next split units

1. memory plus GM agent;
2. TextWorld engine;
3. Quest-CVCD;
4. tests and docs;
5. GameQualityScore benchmark;
6. Markdown/JSON/YAML validators.
