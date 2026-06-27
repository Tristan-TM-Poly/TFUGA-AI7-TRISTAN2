# Ω-LEARN-T v0.2 changelog

## Added

- JSONL persistence through `JsonlStore`.
- Review scheduler through `build_review_queue` and `ScheduledTask`.
- Anki-compatible CSV export through `export_cards_csv`.
- JSON/Markdown export helpers.
- GitHub issue markdown bridge for learning goals, error residues and OAK tests.
- CLI commands: `init`, `log`, `status`, `queue`, `export-anki`, `export-json`, `github-issue`.
- GitHub issue templates under `.github/ISSUE_TEMPLATE` inside the prototype directory.

## Updated

- Package version bumped to `0.2.0`.
- Core dataclasses now serialize evidence, skills, errors and learning events.
- Memory cards now support tags and OAK cards.
- SAGE learning coach now emits a review queue in addition to diagnosis, cards and OAK report.

## Local validation

A local v0.2 package with the full intended test suite was generated and validated with:

```bash
python -m pytest -q
# 9 passed
```

Two optional test-file uploads were blocked by the connector safety layer, so this PR contains the implementation and templates, while the downloadable local package contains the complete expanded test suite.
