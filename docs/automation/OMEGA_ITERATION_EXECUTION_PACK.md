# Omega Iteration Execution Pack

`omega_iteration_execution_pack.py` converts a selected iteration batch into an execution-ready package.

## Input

```text
artifacts/iteration_selected_batch/selected_batch.json
```

## Output

```text
artifacts/iteration_execution_pack/
  execution_pack.json
  execution_prompt.md
  impact_input.json
  EXECUTION_PACK.md
```

## Purpose

The pack bridges planning and action:

1. selected batch from 1024 candidates;
2. execution prompt for ChatGPT/GitHub;
3. file plan;
4. test plan;
5. OAK gates;
6. residue plan;
7. impact analyzer input.

## Run

```bash
python scripts/omega_iteration_execution_pack.py \
  --selected-batch artifacts/iteration_selected_batch/selected_batch.json \
  --config configs/omega_iteration_execution_pack.json \
  --out-dir artifacts/iteration_execution_pack
```

## Boundary

The execution pack is still bounded. It does not execute all 1024 candidates. It prepares a reviewable batch for controlled execution.
