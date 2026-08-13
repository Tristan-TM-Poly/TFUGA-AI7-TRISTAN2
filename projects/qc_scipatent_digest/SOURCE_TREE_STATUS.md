# Source Tree Status — PLUS ULTRA v0.3

Status: expanded runnable scaffold added to PR #44 branch.

## Added source tree

```text
projects/qc_scipatent_digest/pyproject.toml
projects/qc_scipatent_digest/qc_scipatent_digest/__init__.py
projects/qc_scipatent_digest/qc_scipatent_digest/models.py
projects/qc_scipatent_digest/qc_scipatent_digest/fixtures.py
projects/qc_scipatent_digest/qc_scipatent_digest/oak_gates.py
projects/qc_scipatent_digest/qc_scipatent_digest/entity_resolution.py
projects/qc_scipatent_digest/qc_scipatent_digest/canon_export.py
projects/qc_scipatent_digest/qc_scipatent_digest/reuse_blueprints.py
projects/qc_scipatent_digest/qc_scipatent_digest/pipeline.py
projects/qc_scipatent_digest/qc_scipatent_digest/cli.py
projects/qc_scipatent_digest/tests/test_pipeline.py
.github/workflows/qc-scipatent-digest-ci.yml
```

## Scope

This source tree is synthetic-fixture-only. It does not fetch live OpenAlex, Crossref, CIPO, WIPO, Lens, or institutional data. It does not make legal, patent, scientific, revenue, freedom-to-operate, or commercialization conclusions.

## Expected synthetic demo counts

```text
documents: 6
opportunities: 6
bridges: 9
```

## OAK lock

Keep PR #44 draft until source tree CI passes and OAK-IP review decides which parts can be public, private, patentable, trade-secret, licensed, blocked, or unknown.
