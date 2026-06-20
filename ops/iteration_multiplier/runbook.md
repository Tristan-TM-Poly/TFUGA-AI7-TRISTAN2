# Omega Iteration Multiplier Runbook

## Generate a full 1024 plan

```bash
python scripts/omega_iteration_multiplier.py \
  --target-count 1024 \
  --batch-size 32 \
  --out-dir artifacts/iteration_multiplier
```

## Generate focused plan

```bash
python scripts/omega_iteration_multiplier.py \
  --target-count 256 \
  --batch-size 16 \
  --focus chatgpt_tristan_v2 \
  --out-dir artifacts/iteration_multiplier_chatgpt
```

## Inspect outputs

```text
iteration_multiplier_manifest.json
ITERATION_MULTIPLIER_DASHBOARD.md
batches/batch_001/prompt.md
batches/batch_001/additions.json
```

## Use with ChatGPT

Open one batch prompt and ask ChatGPT to execute only that bounded batch. Keep the batch size small enough to validate.

## OAK rule

Never execute 1024 file writes blindly. Generate 1024 candidates, then execute bounded batches with tests and review.
