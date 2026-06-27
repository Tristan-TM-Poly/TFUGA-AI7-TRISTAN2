# LanguageGM Rubric-T

LanguageGM Rubric-T is a small evaluation layer for PolyglotLanguageEngine-T.

It scores whether a LanguageGM output is clear, structured, audience-aware, format-correct, and OAK-safe.

## Targets

- clear French;
- clear English;
- teaching explanation;
- pitch draft;
- Markdown documentation;
- JSON contract;
- YAML plan;
- GitHub issue draft;
- review-sensitive caution note.

## Score dimensions

```text
LanguageGMScore = clarity + structure + audience_fit + format_fit + oak_safety + intent_preservation - drift - hidden_claims
```

The score is bounded between 0 and 1.

## Levels

| Score | Level |
|---|---|
| >= 0.90 | master |
| >= 0.80 | strategist |
| >= 0.65 | builder |
| >= 0.50 | apprentice |
| < 0.50 | needs practice |

## OAK boundary

This rubric is an internal training signal. It is not an official language certification and does not replace human review for sensitive claims, public publication, contracts, policy, or IP-related text.

## M+/M-

M+ records what the LanguageGM did well. M- records patterns to avoid in the next draft.
