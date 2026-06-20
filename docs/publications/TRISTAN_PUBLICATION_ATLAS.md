# Tristan Publication Atlas

`omega_tristan_publication_atlas.py` builds OAK-safe publication dossiers that connect Tristan research projects to public university, author, and work metadata.

## Purpose

For each Tristan theory/science, the atlas can generate:

- institution-level research matches;
- public author/professor metadata matches when available through public scholarly APIs;
- relevant public works;
- a Tristan publication package: concept note, paper outline, dataset plan, prototype plan, and OAK validation plan.

## Boundary

This is not an outreach/spam engine.

- It does not send emails.
- It does not scrape private pages.
- It does not claim endorsement or collaboration.
- It uses public metadata only.
- Every match requires human review.
- Submission to a professor, lab, conference, or journal requires a separate review.

## Offline Quebec template

```bash
python scripts/omega_tristan_publication_atlas.py \
  --scope quebec \
  --offline \
  --out-dir artifacts/publication_atlas/quebec_offline
```

## Quebec public metadata run

```bash
python scripts/omega_tristan_publication_atlas.py \
  --scope quebec \
  --max-institutions 20 \
  --max-authors 3 \
  --max-works 5 \
  --top-k 50 \
  --out-dir artifacts/publication_atlas/quebec
```

## Canada public metadata run

```bash
python scripts/omega_tristan_publication_atlas.py \
  --scope canada \
  --max-institutions 80 \
  --max-authors 2 \
  --max-works 4 \
  --top-k 120 \
  --out-dir artifacts/publication_atlas/canada
```

## Outputs

```text
artifacts/publication_atlas/
  publication_atlas_manifest.json
  PUBLICATION_ATLAS.md
  dossiers/
    <institution>/
      <project>__<author>.md
```

## Tristan project keys

- `omega_math_universe`
- `omega_spectro_universe`
- `omega_materials`
- `ait_dynamics`
- `bayes_tristan`
- `hgfm`
- `ait_code_science`

## OAK path

- OAK-3: mapping exists.
- OAK-4: metadata atlas and dossiers generated.
- OAK-5: human review of public metadata and target relevance.
- OAK-6+: professor/lab-specific review, real manuscript, validation package, and explicit consent/collaboration if needed.
