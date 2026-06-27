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

## New split unit: PolyglotLanguageEngine-T

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
- IP caution notes.

### Objects

- `LanguageQuest`
- `LanguageRun`
- `PolyglotLanguageEngine`

### Boundary

PolyglotLanguageEngine-T is an internal drafting and simulation unit. It does not claim official translation, legal advice, patent advice, or external certification.

## Boundary

Omega GAME T is a game, simulation, and research lab. It is not a tool for manipulation, unfair automation, or unsafe real-world instructions.

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
6. PolyglotLanguageEngine follow-ups: language curriculum, LanguageGM rubric, Markdown/JSON/YAML validators.
