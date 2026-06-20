# Response Impact Runbook

## Purpose

Quantify every ChatGPT iteration after it creates or modifies repo artifacts.

## Run analyzer

```bash
python scripts/omega_response_impact_analyzer.py \
  --input configs/response_impact/current_response_input.json \
  --out artifacts/response_impact_report.json
```

## Interpret score

- 0-20: weak
- 21-40: useful
- 41-60: strong
- 61-80: very strong
- 81-100: plus ultra

## OAK rule

A high score means the iteration was operationally useful. It does not prove scientific claims.
