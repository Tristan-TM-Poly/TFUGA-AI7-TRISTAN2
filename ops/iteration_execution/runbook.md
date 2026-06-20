# Iteration Execution Pack Runbook

## Full chain

```bash
python scripts/omega_iteration_multiplier.py \
  --target-count 1024 \
  --batch-size 32 \
  --out-dir artifacts/iteration_multiplier

python scripts/omega_iteration_batch_selector.py \
  --manifest artifacts/iteration_multiplier/iteration_multiplier_manifest.json \
  --batch-size 16 \
  --out-dir artifacts/iteration_selected_batch

python scripts/omega_iteration_execution_pack.py \
  --selected-batch artifacts/iteration_selected_batch/selected_batch.json \
  --out-dir artifacts/iteration_execution_pack
```

## Use

Open `artifacts/iteration_execution_pack/execution_prompt.md` and execute that bounded batch with ChatGPT/GitHub.

## After execution

Run the response impact analyzer on `impact_input.json` or a response-specific impact input.

## OAK rule

Selected batch execution is not validation. Validate files, tests, docs, workflows and residues.
