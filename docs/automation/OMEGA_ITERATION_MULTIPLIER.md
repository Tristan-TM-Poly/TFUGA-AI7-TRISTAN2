# Omega Iteration Multiplier

`omega_iteration_multiplier.py` maximizes the number of useful additions per interaction by generating bounded OAK-safe candidate additions.

## Purpose

Instead of asking for one improvement at a time, the multiplier creates up to 1024 candidate additions and groups them into reviewable batches.

Each candidate contains:

- layer;
- module;
- action;
- candidate files;
- expected tests;
- OAK gates;
- priority;
- residues.

## Run 1024 candidates

```bash
python scripts/omega_iteration_multiplier.py \
  --config configs/omega_iteration_multiplier.json \
  --target-count 1024 \
  --batch-size 32 \
  --out-dir artifacts/iteration_multiplier
```

## Focus one module

```bash
python scripts/omega_iteration_multiplier.py \
  --target-count 256 \
  --batch-size 16 \
  --focus chatgpt_tristan_v2 \
  --out-dir artifacts/iteration_multiplier_chatgpt
```

## Outputs

```text
artifacts/iteration_multiplier/
  iteration_multiplier_manifest.json
  ITERATION_MULTIPLIER_DASHBOARD.md
  batches/
    batch_001/
      prompt.md
      additions.json
```

## OAK boundary

- Candidate plan only.
- Bounded generation.
- Human review for external action.
- Prototype is not proof.
- Data work needs license and provenance review.
- Publication work is review-only and no automatic outreach.

## Operating pattern

1. Generate 1024 candidates.
2. Select top priority batch.
3. Execute one batch with ChatGPT/GitHub.
4. Validate files and tests.
5. Feed residues back into M-minus.
6. Generate next 1024 candidates with new focus.
