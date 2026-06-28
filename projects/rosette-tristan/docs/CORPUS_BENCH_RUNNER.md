# Rosette Corpus Bench Runner

`rosette-corpus-bench` executes an annotated `corpus_manifest.json` and verifies extraction results against expected counts and trace requirements.

## Workflow

```bash
rosette-bench-corpus init --out rosette_corpus
rosette-corpus-bench rosette_corpus/corpus_manifest.json --out out_corpus_bench
```

## Output

```text
out_corpus_bench/
  corpus_bench_report.json
  cases/
    clean_text_001/
    paged_text_001/
```

## What it checks

Per case, it runs Rosette Fidelity and records:

- blocks
- equations
- claims
- page refs
- bboxes

Then it compares those counts to the case expectations:

- `min_blocks`
- `min_equations`
- `min_claims`
- `requires_page_refs`
- `requires_bboxes`
- `requires_visual_oak`

## OAK statuses

- `corpus_bench_passed_not_certified`
- `corpus_bench_failed_expectations`
- `corpus_bench_invalid_manifest`

## OAK lock

Corpus Bench validates extraction expectations, not scientific truth. Real certification requires licensed ground-truth corpora, source page/bbox annotations, expected equations/tables/figures/claims, and independent review.
