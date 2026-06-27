# RosetteBench

RosetteBench measures whether Rosette-Tristan converts documents into useful, traceable and falsifiable artifacts.

## Benchmark families

| Family | Purpose |
|---|---|
| `txt_clean` | deterministic extraction and OAK report baseline |
| `pdf_digital` | page text extraction with source refs |
| `pdf_two_column` | layout and reading-order stress |
| `equation_heavy` | LaTeX reconstruction and render-diff-repair |
| `table_heavy` | table structure fidelity |
| `figure_heavy` | figure/caption/evidence linking |
| `patent_claims` | claim segmentation, IP-safe summaries |
| `old_scan` | OCR uncertainty and M⁻ capture |

## Metrics

```yaml
text_cer: character error rate when ground truth exists
layout_order_score: paragraph/section order fidelity
equation_exact_match: exact LaTeX match when ground truth exists
equation_semantic_score: symbolic/structural equivalence proxy
table_structure_f1: rows, columns and cells
citation_accuracy: DOI/reference/source matching
claim_grounding: fraction of claims linked to explicit evidence
code_execution_rate: generated code files import/run without unsafe assumptions
test_pass_rate: generated tests passing
reproduction_status: exact/qualitative/synthetic/missing-data/failed
oak_honesty: uncertain artifacts correctly marked uncertain
```

## Minimal acceptance gates

A Rosette run can be called `research-usable` only when:

1. every artifact has a source trace;
2. uncertain equations/claims are marked uncertain;
3. generated code refuses silent execution when translation is incomplete;
4. M⁻ records at least the major unresolved risks;
5. public outputs avoid copyright-risky long reproduction.

## First baseline

The first benchmark is intentionally humble:

```bash
rosette compile examples/sample_paper.txt --out out --mode strict
pytest -q
```

Expected: one equation, at least one claim candidate, OAK warnings for uncertified equation and evidence-free claims.
