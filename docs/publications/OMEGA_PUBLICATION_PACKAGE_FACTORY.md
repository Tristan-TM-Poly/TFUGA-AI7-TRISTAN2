# Omega Publication Package Factory

`omega_publication_package_factory.py` transforms a Tristan Publication Atlas manifest into reviewable publication packages.

## What it generates

For each selected university/public-author/project match, the factory writes:

```text
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

This is a publication-preparation engine, not an outreach engine.

- It does not send messages.
- It does not imply endorsement.
- It does not claim collaboration.
- It produces review-only drafts.
- Every package requires human review.

## Example

First build an atlas:

```bash
python scripts/omega_tristan_publication_atlas.py \
  --scope quebec \
  --offline \
  --out-dir artifacts/publication_atlas
```

Then build packages:

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
artifacts/publication_packages/
  publication_package_manifest.json
  PUBLICATION_PACKAGE_DASHBOARD.md
  packages/<institution>/<project>/<public-author>/...
```

## OAK path

- OAK-3: templates and package definitions.
- OAK-4: generated packages from atlas artifacts.
- OAK-5: human review of each package.
- OAK-6+: real manuscript, target-specific review, consent/collaboration when applicable.
