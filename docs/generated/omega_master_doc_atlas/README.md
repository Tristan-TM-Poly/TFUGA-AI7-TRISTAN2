# Ω-MASTER-DOC-ATLAS-T∞ generated source registry

This directory stores a compact, commit-addressed source registry extracted from six successful Ω-DOC-FACTORY R1.0 GitHub Actions artifacts. The registry retains repository commit, campaign fingerprint, artifact ID/digest, derived module-overlap receipts, component candidates, claim summaries and evidence-count metadata needed to regenerate the global atlas without committing the original ZIP archives.

Regenerate with:

```bash
python -m omega_latex_t.master_doc_atlas_cli \
  --registry docs/generated/omega_master_doc_atlas/source-registry.json \
  --output-dir generated/omega_master_doc_atlas
```

OAK: `ARTIFACT_ARCHIVED != INDEPENDENT_REPLICATION`; `REVIEW_BINDING_VOLUME != EVIDENCE_STRENGTH`.
