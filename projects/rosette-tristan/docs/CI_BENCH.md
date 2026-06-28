# Rosette CI Bench

The Rosette-Tristan CI now runs more than unit tests. It also executes smoke benchmark CLIs and uploads their reports as GitHub Actions artifacts.

## CI commands

```bash
pytest -q
rosette-bench --out out_bench
rosette-bench-corpus init --out out_corpus
rosette-corpus-bench out_corpus/corpus_manifest.json --out out_corpus_bench
```

## Uploaded reports

The workflow uploads these files as the `rosette-ci-reports` artifact:

```text
projects/rosette-tristan/out_bench/rosette_bench_report.json
projects/rosette-tristan/out_corpus/corpus_manifest.json
projects/rosette-tristan/out_corpus_bench/corpus_bench_report.json
```

## OAK lock

Passing CI proves the local package installs, unit tests pass, benchmark smoke tests run, and report files are produced. It does not prove real-world PDF fidelity, scientific truth, or benchmark certification.
