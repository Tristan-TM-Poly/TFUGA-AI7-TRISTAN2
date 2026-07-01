# Ω-AUTO²-OAK-FIXALL-T Batch Report Runbook

The batch report layer turns one or more local decision JSON files into a dry-run summary.

It is not a merge engine. It is a visibility layer for M+/M− learning.

## Commands

```bash
python automation/oak_fixall/batch_report.py \
  automation/oak_fixall/examples/hyperatlas_safe_extraction.decision.json
```

Generate files:

```bash
python automation/oak_fixall/batch_report.py \
  automation/oak_fixall/examples/hyperatlas_safe_extraction.decision.json \
  --json-out reports/oak_fixall/example_summary.json \
  --md-out reports/oak_fixall/example_summary.md
```

## OAK boundary

The report may identify `MERGE_NOW` candidates, but it cannot authorize a merge alone.

Live merge still requires:

```text
open=true
draft=false
mergeable=true
checks=green
scope=coherent
risk=low
head_sha_locked=true
```

## Why this exists

Repeated GitHub loops need a compact way to see blocker classes across many items without mutating repositories. This batch layer makes the next action visible before any action is taken.
