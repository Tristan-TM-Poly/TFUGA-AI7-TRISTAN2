# Ω-INTENT-TO-EVERYTHING-T∞ R0.3 — RepoTwin, CI Impact Router and Proof-Carrying Artifacts

## Purpose

R0.3 attacks the infrastructure bottleneck observed while validating R0.2: a small
change to a global project file can trigger many historical workflows in the
monorepo. The solution is not to claim infinite CI capacity. It is to construct a
deterministic repository twin, calculate the conservative impact closure of a
change, and route focused, integration and full validation separately.

```text
repository
→ deterministic file inventory
→ Python import graph
→ test-to-package edges
→ workflow path filters
→ changed paths
→ reverse dependency closure
→ focused tests
→ integration packages
→ selected workflows
→ full-suite escalation when required
→ proof-carrying report
```

## RepoTwin

`RepoTwinScanner` records for every non-ignored file:

- normalized path;
- SHA-256 and byte size;
- artifact kind;
- owning top-level package;
- Python import roots when parseable;
- generated-output status.

It also extracts conservative workflow path patterns and whether the workflow
contains `cancel-in-progress: true`. The manifest is deterministic for identical
repository content and carries a root digest.

## Impact routing

`ImpactRouter` accepts a RepoTwin manifest and one or more changed paths. It
computes:

- directly changed packages;
- reverse dependency closure;
- tests importing affected packages;
- workflows whose declared path filters match;
- unknown paths and global-contract changes;
- a tiered validation plan;
- a relative cost heuristic.

The validation tiers are:

1. `focused` — directly mapped tests;
2. `integration` — affected package closure and selected workflows;
3. `nightly_or_manual_full` — global contracts, broad impact or unknown package roots.

The cost score is a planning heuristic. It is not a monetary bill, exact runtime
prediction or provider-capacity guarantee.

## Proof-carrying artifacts

`ProofArtifactBuilder` wraps a generated or validated file with:

- content hash and size;
- media type;
- immutable provenance;
- parent requirements, plans or intentions;
- validation receipts;
- epistemic status;
- uncertainty and risks;
- publication authorization state.

Verification detects content changes after the envelope was created. A passing
hash check proves content identity only; it does not prove scientific truth or
software correctness.

## OAK boundary

R0.3 does not:

- execute arbitrary CI jobs;
- mutate workflow files automatically;
- guarantee that static imports capture every runtime dependency;
- replace full integration testing when global contracts change;
- infer scientific truth from file hashes;
- authorize publishing, merging or spending compute;
- claim that a relative cost score is an exact runtime.

Dynamic imports, generated code, non-Python dependencies and external CI systems
remain explicit uncertainty sources.

## Commands

```bash
python -m omega_intent_t.r03 scan . --output /tmp/repotwin.json
python -m omega_intent_t.r03 route . \
  --changed omega_intent_t/r03/router.py \
  --changed tests/test_omega_intent_r03.py \
  --output /tmp/impact.json
python -m omega_intent_t.r03 proof omega_intent_t/r03/router.py \
  --root . \
  --provenance INTENT-R03 \
  --validator pytest \
  --validation-status passed \
  --validation-command "pytest -q tests/test_omega_intent_r03.py"
python -m omega_intent_t.r03 oak
```

## Integration strategy

R0.3 deliberately uses `python -m omega_intent_t.r03` and does not add another
project script entry. This avoids modifying `pyproject.toml` merely to expose a
new wave and demonstrates the single-entry/registry direction proposed for a
future repository-wide CLI migration.
