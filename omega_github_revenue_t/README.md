# OAKSponsorOS-T R0.1

`omega_github_revenue_t` is the executable kernel for Ω-GITHUB-REVENUE-T∞.

It converts bounded GitHub artifacts into reviewable assessments, offers, sponsor-tier sustainability checks, experiments, capital-allocation candidates, and privacy-minimized revenue events.

## Quick start

```bash
python -m omega_github_revenue_t.cli demo
python -m pytest tests/test_omega_github_revenue_t.py
```

Stream a JSONL frontier without a fixed total-item ceiling:

```bash
omega-github-revenue audit examples/data/revenue_artifacts.jsonl \
  --output generated/omega_github_revenue/audit.jsonl \
  --minimum-score 0.35
```

Append a privacy-minimized revenue event:

```bash
omega-github-revenue ledger event.json \
  --ledger private-local-path/revenue-ledger.jsonl
```

Do not commit the resulting ledger when it contains real financial events. The implementation rejects forbidden banking and credential field names, but that is only a defense-in-depth control, not a complete DLP system.

## Implemented contracts

- typed artifact, evidence, offer, sponsor-tier, experiment, and revenue-event models;
- evidence-weighted value scoring;
- fail-closed disclosure/IP/privacy gate;
- bounded offer compiler;
- sponsor-tier maintenance sustainability test;
- scale/revise/stop/continue experiment decision;
- evidence-weighted capital allocation;
- lazy JSONL frontier processing;
- hash-chained append-only ledger;
- explicit rejection of banking, tax-ID, credential, and home-address fields.

## OAK limits

The score is a prioritization heuristic. It is not a truth probability, valuation, credit decision, tax calculation, legal opinion, product-market-fit proof, or revenue forecast.

No network calls, public messages, GitHub mutations, Stripe operations, bank transfers, invoices, or payments occur in this package.
