# Response Score History Runbook

## Build dashboard

```bash
python scripts/omega_response_score_history.py \
  --inputs-dir configs/response_impact \
  --out-dir artifacts/response_score_history
```

## Inspect

```text
artifacts/response_score_history/RESPONSE_SCORE_HISTORY.md
artifacts/response_score_history/response_score_history.json
```

## Use after each response

1. Add or update a response impact input JSON.
2. Run the response impact analyzer for that response.
3. Run this score history builder.
4. Compare latest score and trend.
5. Add residues to M-minus.

## OAK rule

A rising score means better operational process, not proof of scientific claims.
