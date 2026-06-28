# RosetteBench Corpus

`rosette-bench-corpus` defines and validates annotated benchmark corpora for Rosette.

This layer does not add copyrighted PDFs. It creates a safe manifest format and synthetic starter corpus so real datasets can be added later with explicit license and ground-truth annotations.

## Initialize a minimal synthetic corpus

```bash
rosette-bench-corpus init --out rosette_corpus
```

## Validate an existing corpus manifest

```bash
rosette-bench-corpus validate rosette_corpus/corpus_manifest.json --out corpus_validation.json
```

## Manifest shape

```json
{
  "name": "rosette_minimal_annotated_corpus",
  "version": "0.1.0",
  "cases": [
    {
      "case_id": "paged_text_001",
      "case_type": "paged_text",
      "path": "cases/paged_text.txt",
      "license": "synthetic",
      "source": "synthetic_or_user_supplied",
      "expected": {
        "min_blocks": 2,
        "min_equations": 1,
        "min_claims": 1,
        "requires_page_refs": true
      }
    }
  ]
}
```

## Supported case types

- `clean_text`
- `paged_text`
- `pdf_digital`
- `pdf_two_column`
- `equation_heavy`
- `table_heavy`
- `figure_heavy`
- `scanned_pdf`
- `patent_claims`
- `old_math_scan`

## OAK lock

Synthetic cases only prove pipeline coherence. Real RosetteBench certification requires licensed corpora, ground-truth annotations, source page/bbox refs, expected equations/tables/figures/claims, and independent review.
