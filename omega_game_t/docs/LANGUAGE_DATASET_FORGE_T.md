# LanguageDatasetForge-T

LanguageDatasetForge-T builds a small internal dataset from the Omega GAME T language stack.

## Purpose

It turns curriculum quests into structured records that can be used for internal benchmarking and regression checks.

## Core loop

```text
CurriculumQuest -> LanguageRun -> LanguageGMEvaluation -> ValidationReport -> RepairLoopResult -> DatasetItem
```

## Dataset item

Each item stores:

- quest;
- raw language run;
- rubric evaluation;
- validation report;
- repair result;
- tags;
- score summary.

## Uses

- compare LanguageGM outputs;
- find weak tracks;
- track M+/M-;
- benchmark format validation;
- build small reviewable fixtures for tests.

## Boundary

This is an internal dataset forge for small synthetic training and benchmark examples. It does not publish data, scrape external sources, or claim real-world certification.
