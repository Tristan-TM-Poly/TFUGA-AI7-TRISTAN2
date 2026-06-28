# RosetteBench Runner

`rosette-bench` runs a minimal synthetic OAK benchmark for Rosette.

It is designed as a smoke-test benchmark, not a proof of real-world PDF performance.

## Command

```bash
rosette-bench --out out_bench
```

## Outputs

```text
out_bench/
  rosette_bench_report.json
  fixtures/
    clean_text.txt
    paged_text.txt
  cases/
    clean_text/
    paged_text/
    visual_match/
```

## Cases

- `clean_text`: text fixture with one claim and equation.
- `paged_text`: page-marker fixture with source refs.
- `visual_match`: generated source crop matched against Visual OAK.

## Metrics

- `text_fidelity`
- `layout_fidelity`
- `page_ref_coverage`
- `equation_render_score`
- `claim_grounding_rate`
- `oak_honesty_score`

## OAK lock

Synthetic fixtures are not proof of real PDF performance. A future RosetteBench must add real PDFs, scanned PDFs, tables, figures, patents, old scans and ground-truth annotations.
