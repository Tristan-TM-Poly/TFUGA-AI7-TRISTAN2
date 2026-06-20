# Omega Publication Package Factory Runbook

## Purpose

Convert Tristan Publication Atlas matches into review-only publication packages.

## Build atlas first

```bash
python scripts/omega_tristan_publication_atlas.py \
  --scope quebec \
  --offline \
  --out-dir artifacts/publication_atlas
```

## Build packages

```bash
python scripts/omega_publication_package_factory.py \
  --atlas-manifest artifacts/publication_atlas/publication_atlas_manifest.json \
  --templates configs/tristan_publication_package_templates.json \
  --out-dir artifacts/publication_packages \
  --min-score 0 \
  --top-k 50
```

## Outputs

```text
publication_package_manifest.json
PUBLICATION_PACKAGE_DASHBOARD.md
packages/<institution>/<project>/<public-author>/
  00_PACKAGE_INDEX.md
  01_ABSTRACT_SEED.md
  02_PAPER_OUTLINE.md
  03_DATASET_PLAN.md
  04_PROTOTYPE_PLAN.md
  05_OAK_VALIDATION_PLAN.md
  06_HUMAN_REVIEW_CHECKLIST.md
  07_COLLABORATION_NOTE_DRAFT_REVIEW_ONLY.md
  package.json
```

## Boundary

The collaboration note is review-only. Do not send it automatically. Human review is mandatory before any contact, submission, or public claim.
