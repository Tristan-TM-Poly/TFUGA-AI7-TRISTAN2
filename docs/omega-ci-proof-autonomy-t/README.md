# Ω-CI-PROOF-AUTONOMY-T∞ R0.1

This package crystallizes autonomy levels **A1 through A3**:

1. **A1 — proof-producing CI**: claims, proof plans, Evidence Bundles, content hashes and a Merkle evidence root;
2. **A2 — adaptive CI**: consumes RepoTwin/ImpactPlan output and selects affected claims, tests and environments;
3. **A3 — generative CI**: produces deterministic regression-test candidates from structured M-minus rules.

## OAK boundary

R0.1 does **not** autonomously patch code, push branches, merge pull requests, publish releases or authorize scientific claims. `AutonomyGate` rejects A4–A7 and always returns `automatic_merge_allowed=false`.

The JSONL ledger is a deterministic integrity chain, not a digital identity signature. Evidence quality scores are heuristics, not probabilities of correctness. Static impact analysis does not exhaustively detect dynamic imports or runtime reflection.

## Pipeline

```text
RepoTwin impact plan
→ claim registry
→ proof plan
→ selected and missing tests
→ finite CI execution
→ Evidence Bundle
→ Merkle root
→ append-only proof ledger
→ OAK audit
→ human-reviewed promotion
```

## Commands

```bash
python -m omega_ci_proof_t plan \
  --impact data/omega_ci_proof_t/sample-impact.json \
  --claims data/omega_ci_proof_t/claims.json \
  --tests data/omega_ci_proof_t/tests.json \
  --output generated/proof-plan.json

python -m omega_ci_proof_t generate-regressions \
  --mminus data/omega_ci_proof_t/mminus.json \
  --output generated/test_mminus_regressions.py

python -m omega_ci_proof_t bundle \
  --plan generated/proof-plan.json \
  --results data/omega_ci_proof_t/sample-results.json \
  --commit-sha local-fixture \
  --output generated/evidence-bundle.json \
  --ledger generated/proof-ledger.jsonl

python -m omega_ci_proof_t verify \
  --bundle generated/evidence-bundle.json \
  --plan generated/proof-plan.json

python -m omega_ci_proof_t autonomy --level A4
```

The final command must be denied in R0.1.

## Proof semantics

A green workflow is only a summary. The durable result is the Evidence Bundle containing the plan digest, test receipts, properties, artifact hashes, limitations, decision and Merkle root.
