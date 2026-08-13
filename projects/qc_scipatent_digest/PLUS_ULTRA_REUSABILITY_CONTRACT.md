# PLUS ULTRA Reusability Contract

Every future QC SciPatent artifact should be reusable as at least one of:

- Python module;
- CLI command;
- JSON schema;
- SQLite table;
- Markdown report;
- dashboard panel;
- DCT++ canon card;
- GitHub issue;
- OAK review item;
- invention disclosure draft;
- product/service blueprint.

## Required metadata

Each reusable output should include:

- source;
- license/copyright status;
- OAK status;
- IP classification;
- next validation action;
- M- risks/errors to avoid;
- GitHub path or artifact checksum.

## Default command shape

```bash
python -m qc_scipatent_digest.cli plus-ultra --out outputs/plus_ultra
```

## Default OAK status

Unless reviewed, generated opportunities are `internal_review_required`.
