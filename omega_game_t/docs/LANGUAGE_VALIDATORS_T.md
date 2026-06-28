# LanguageValidators-T

LanguageValidators-T adds structural checks for PolyglotLanguageEngine-T outputs.

It helps LanguageGM verify that a draft is not only clear, but also shaped correctly for its target format.

## Validators

- Markdown validator;
- JSON contract validator;
- YAML plan validator;
- GitHub issue draft validator.

## Core loop

```text
LanguageRun -> LanguageValidator -> ValidationReport -> M+/M- -> next repair quest
```

## What it checks

### Markdown

- title heading;
- section headings;
- OAK or boundary section;
- enough body content.

### JSON

- starts and ends like JSON object;
- has intent/audience/status/OAK-like fields;
- no obvious empty object.

### YAML

- key-value structure;
- status field;
- OAK or constraints field;
- enough lines.

### GitHub issue draft

- goal section;
- notes or context section;
- OAK/review/checks section.

## Boundary

This is a lightweight structural validator. It is not a full parser, compiler, policy checker, legal reviewer, or official quality certification.

## Output

The validator returns:

- format name;
- valid boolean;
- score between 0 and 1;
- passed checks;
- failed checks;
- M+;
- M-;
- next repair quest.
