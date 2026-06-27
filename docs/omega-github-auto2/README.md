# Ω-GitHub-AUTO² Top1024 Control Plane

This folder defines the GitHub-native automation layer for the Omega ecosystem.

## Purpose

Turn the Top64 / Top256 / Top1024 expansion matrix into deterministic GitHub artifacts:

- Top1024 card manifest
- Top64 execution queue
- issue-draft Markdown files
- OAK report
- unit-tested factory script
- manual GitHub Actions workflow

The system is intentionally offline by default. It generates plans, queues, and reviewable artifacts without contacting customers, activating billing, disclosing sensitive IP, or merging code automatically.

## Canonical strategy

```text
Sell SPECTRA.
Retain with LEARN / M-.
Protect ECC until benchmarked.
```

## Files

- `configs/omega_github_auto2_top1024.json` — 16 domains × 4 sectors × 16 atoms = 1024 cards.
- `scripts/omega_github_auto2_factory.py` — deterministic generator.
- `tests/test_omega_github_auto2_factory.py` — OAK invariants for card count, P0 queue, and review locks.
- `.github/workflows/omega-github-auto2-factory.yml` — manual workflow to generate and print the queue.

## Run locally

```bash
python scripts/omega_github_auto2_factory.py \
  --config configs/omega_github_auto2_top1024.json \
  --out artifacts/omega_github_auto2 \
  --issue-limit 16

python -m unittest tests/test_omega_github_auto2_factory.py
```

## OAK locks

The generated automation must keep human review for:

- merge to `main`
- external outreach
- patentable or trade-secret disclosure
- production billing changes
- regulated claims
- destructive repository operations

## Expansion logic

Each sector becomes 16 cards:

1. input schema
2. output schema
3. core algorithm
4. validator
5. anomaly detector
6. corrector or reconstructor
7. confidence score
8. OAK gate
9. benchmark suite
10. failure mode registry
11. M- logger
12. API endpoint
13. batch processor
14. dashboard card
15. customer report
16. pricing meter

## Next layer

The next safe automation step is to add a second workflow that opens one draft issue per selected P0 card. That should remain explicit and rate-limited, not a silent mass-issue generator.
