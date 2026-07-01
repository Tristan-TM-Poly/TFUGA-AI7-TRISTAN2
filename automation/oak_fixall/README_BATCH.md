# FixAll Batch Quickstart

Run the local dry-run batch report against the example fixture list:

```bash
python automation/oak_fixall/batch_report.py \
  $(cat automation/oak_fixall/examples/batch_input_list.txt) \
  --json-out reports/oak_fixall/example_summary.json \
  --md-out reports/oak_fixall/example_summary.md
```

The output summarizes decisions and blockers. It does not mutate repositories.

Use it before a GitHub action loop to see repeated blocker classes at a glance.
