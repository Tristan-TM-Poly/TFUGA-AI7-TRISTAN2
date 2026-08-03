# OAKSponsorOS-T R0.2 MAX

`omega_github_revenue_t` is the executable kernel for **Ω-GITHUB-REVENUE-T∞**.

It turns bounded GitHub research artifacts into reviewable assessments, offers, Sponsor-tier sustainability checks, authorized repository audits, proof receipts, finite adaptive campaigns, conversion evidence, privacy-minimized reconciliation, pricing hypotheses, and dependency-aware resource decisions.

## Quick start

```bash
python -m pytest -q \
  tests/test_omega_github_revenue_t.py \
  tests/test_omega_github_revenue_r02.py

python -m omega_github_revenue_t.cli demo
python -m omega_github_revenue_t.r02_cli atlas
python -m omega_github_revenue_t.r02_cli profile \
  --output generated/sponsor-profile
```

## Authorized OAKGate audit

OAKGate refuses to run without an explicit authorization assertion and a repository-bound receipt.

```bash
omega-github-revenue-r02 oakgate-audit . \
  --output generated/oakgate-audit \
  --authorization-id AUTH-LOCAL-001 \
  --granted-by Tristan-TM-Poly \
  --granted-at 2026-08-03T02:00:00Z \
  --i-am-authorized
```

Outputs:

```text
audit-report.json
audit-report.md
authorization-receipt.json
evidence-manifest.json
run-receipt.json
```

The audit is static and local. It performs no network request, repository mutation, dependency execution, security certification, legal certification, or commercial claim.

## Adaptive finite campaigns

R0.2 has no permanent global item-count ceiling. Every run remains finite and is bounded by its input, available compute/storage, and optional stop budget.

```bash
omega-github-revenue-r02 campaign \
  --count 100000 \
  --database generated/revenue-capacity.sqlite \
  --campaign-id capacity-100k \
  --checkpoint-every 10000
```

The campaign provides lazy generation, adaptive batches, SQLite WAL state, batch upserts, deduplication, quarantine, checkpoints, resume, and a SHA-256 Merkle content root.

Synthetic fixtures validate capacity only. They are not customers, sponsors, revenue, scientific results, inventions, or market traction.

## Conversion and reconciliation

```bash
omega-github-revenue-r02 funnel \
  examples/data/revenue_funnel_snapshot.json

omega-github-revenue-r02 reconcile \
  examples/data/revenue_events_internal.json \
  examples/data/revenue_events_provider.json
```

The funnel engine reports observed ratios and simple Beta posterior uncertainty. The reconciliation engine detects missing, duplicated, or mismatched minimized provider events. Neither replaces analytics attribution, bank statements, tax filings, or professional accounting.

## R0.1 contracts retained

```bash
omega-github-revenue audit examples/data/revenue_artifacts.jsonl \
  --output generated/omega_github_revenue/audit.jsonl \
  --minimum-score 0.35
```

R0.1 continues to provide:

- typed artifact, evidence, offer, Sponsor-tier, experiment, and revenue-event models;
- evidence-weighted value scoring;
- fail-closed disclosure/IP/privacy gates;
- bounded offer compilation;
- Sponsor-tier maintenance sustainability checks;
- scale/revise/stop/continue experiment decisions;
- evidence-weighted capital allocation;
- lazy JSONL frontier processing;
- a hash-chained append-only ledger;
- rejection of banking, tax-ID, credential, and residential-address fields.

## R0.2 MAX contracts

- explicit expiring audit authorization;
- local repository matching and operation scopes;
- secret-pattern detection with fingerprints rather than secret disclosure;
- deterministic OAKGate repository reports;
- canonical hashes, Merkle roots, and inclusion proofs;
- durable SQLite campaigns and checkpoints;
- adaptive finite frontiers beyond arbitrary 10k limits;
- Bayesian conversion-stage decision aids;
- privacy-minimized provider reconciliation;
- delivery-cost and contribution-margin hypotheses;
- deterministic Sponsor profile and tier bundle generation;
- Pareto and dependency-aware portfolio allocation;
- machine-readable revenue/evidence atlas;
- CI on Python 3.10 and 3.13 plus a 100,000-artifact capacity job.

## Private financial data

Do not commit real revenue ledgers or campaign databases when they contain private commercial observations. No bank account number, transit number, institution number, void cheque, tax identifier, home address, API secret, Stripe credential, or confidential client payload belongs in this repository.

Banking and tax configuration remains exclusively inside authorized GitHub, Stripe, banking, accounting, and government interfaces.

## OAK limits

Every score is a prioritization heuristic. It is not a truth probability, security rating, company valuation, credit decision, tax calculation, legal opinion, product-market-fit proof, or revenue forecast.

No public message, GitHub Sponsors publication, contract acceptance, invoice, payment, bank transfer, tax filing, patent disclosure, or third-party private-repository inspection occurs autonomously in this package.

See `docs/OMEGA_GITHUB_REVENUE_R02_MAX.md` for the full architecture, failure memory, validation protocol, and R0.3 promotion gate.
