# Omega Response Score History

`omega_response_score_history.py` builds a history dashboard from response impact inputs and reports.

## Purpose

Track quantitative process improvement after each ChatGPT/GitHub iteration.

The dashboard reports:

- response count;
- average score;
- best score;
- latest score;
- trend from first to latest;
- plus-ultra count;
- per-response records.

## Run

```bash
python scripts/omega_response_score_history.py \
  --inputs-dir configs/response_impact \
  --out-dir artifacts/response_score_history
```

## Outputs

```text
artifacts/response_score_history/
  response_score_history.json
  RESPONSE_SCORE_HISTORY.md
```

## OAK boundary

Scores are operational process signals. They are not scientific validation, proof, or external endorsement.
