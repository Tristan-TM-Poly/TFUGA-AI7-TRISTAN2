# LanguageRepairLoop-T

LanguageRepairLoop-T turns LanguageValidators-T failed checks into targeted repair steps.

## Core loop

```text
LanguageRun -> ValidationReport -> failed checks -> repair actions -> improved LanguageRun -> ValidationReport
```

## Purpose

The goal is to make LanguageGM drafts improve through small deterministic repair steps.

## Inputs

- `LanguageRun`
- target validation score
- maximum attempts

## Outputs

- final run;
- final validation report;
- repair attempts;
- convergence flag;
- M+/M-;
- next action.

## Supported repairs

- Markdown title, headings, OAK notes, body length;
- JSON intent, audience, status, OAK fields;
- YAML key-value structure, status, OAK fields;
- GitHub issue goal, notes/context, review/checks;
- generic draft length and review note.

## OAK boundary

This loop is an internal draft improvement tool. It produces training signals and review notes only.

## Reviewable split

This is intentionally small and deterministic so it can be tested and reviewed as a split unit.
