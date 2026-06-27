# Omega GitHub AUTO2 Top1024 Control Plane

This is the GitHub-native automation layer for the Omega ecosystem.

## Mission

Turn the Top64 / Top256 / Top1024 expansion matrix into deterministic GitHub artifacts:

- Top1024 manifest
- Top16 immediate queue
- Top64 execution queue
- issue-draft Markdown files
- PR-draft Markdown files
- Codex task packs
- OAK tribunal report
- dependency graph
- dashboard
- M-minus registry seed
- repo routing manifest
- GitHub label manifest

The system is offline by default. It generates plans, queues, review artifacts, and evidence without contacting customers, activating billing, disclosing sensitive IP, or merging code automatically.

## Canonical strategy

```text
Sell SPECTRA.
Retain with LEARN / M-.
Protect ECC until benchmarked.
```

## Files

- `configs/omega_github_auto2_top1024.json` — 16 domains x 4 sectors x 16 atoms = 1024 cards.
- `configs/omega_github_auto2_states.json` — state machine and human-lock policy.
- `scripts/omega_github_auto2_factory.py` — deterministic v2 factory.
- `tests/test_omega_github_auto2_factory.py` — unit tests for invariants and locks.
- `.github/workflows/omega-github-auto2-factory.yml` — manual workflow.
- `.github/ISSUE_TEMPLATE/omega_auto2_card.yml` — card issue template.
- `docs/omega-github-auto2/CARD_CONTRACT.md` — card contract.
- `docs/omega-github-auto2/OAK_TRIBUNAL.md` — OAK tribunal.
- `docs/omega-github-auto2/HUMAN_LOCKS.md` — human locks.
- `docs/omega-github-auto2/ROADMAP.md` — roadmap.

## Run locally

```bash
python scripts/omega_github_auto2_factory.py \
  --config configs/omega_github_auto2_top1024.json \
  --out artifacts/omega_github_auto2 \
  --issue-limit 16 \
  --mode materialize

python -m unittest tests/test_omega_github_auto2_factory.py
```

## Modes

- `dry-run`: validate invariants only.
- `plan`: generate manifest, queues, dashboard, OAK report, dependency graph, labels, routing, and M-minus seed.
- `materialize`: all of `plan`, plus issue drafts, PR drafts, and Codex task packs.

## OAK locks

Human review remains mandatory for:

- merge to `main`
- external outreach
- patentable or trade-secret disclosure
- production billing changes
- regulated claims
- destructive repository operations
- customer/private data publication

## Expansion grammar

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
11. M-minus logger
12. API endpoint
13. batch processor
14. dashboard card
15. customer report
16. pricing meter

## OAK principle

```text
No irreversible action from automation.
```

The reactor may draft, rank, test, and recommend. It must not merge, publish sensitive IP, activate billing, or make regulated claims without approval.
