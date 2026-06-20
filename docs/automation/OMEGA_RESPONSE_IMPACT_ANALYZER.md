# Omega Response Impact Analyzer

`omega_response_impact_analyzer.py` gives a quantitative score after each response or iteration.

## Score axes

The score is out of 100:

- artifact_count: concrete files created or updated;
- diversity: distinct artifact categories;
- oak_safety: OAK, review, bounded, prototype/proof, license and residue markers;
- automation: scripts and workflows;
- testability: tests and validators;
- strategic_value: connection to high-value Tristan modules;
- reuse: configs, schemas, templates, manifests and examples.

## Example input

```json
{
  "artifacts": ["scripts/x.py", "tests/test_x.py", ".github/workflows/x.yml"],
  "summary": "OAK bounded workflow with tests",
  "tests": ["unit"],
  "workflows": ["ci"],
  "residues": ["remote run not confirmed"]
}
```

## Run

```bash
python scripts/omega_response_impact_analyzer.py \
  --input configs/response_impact/current_response_input.json \
  --axes configs/omega_response_impact_axes.json \
  --out artifacts/response_impact_report.json
```

## Boundary

The score is an operational heuristic, not scientific validation. It measures process quality and leverage, not truth.
