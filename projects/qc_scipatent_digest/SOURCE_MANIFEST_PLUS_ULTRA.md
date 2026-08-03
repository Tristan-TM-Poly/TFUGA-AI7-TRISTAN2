# Ω-SCI-PATENT-QC-DIGEST-T — PLUS ULTRA source manifest

This manifest records the v0.3 local source package and its high-level additions.

## Package

```text
qc_scipatent_digest_plus_ultra.zip
SHA-256: e48aed805f9aa62d6c665ef137189aeeb1bac2504bd6c27185146636e93749ff
```

## New v0.3 source modules

| Module | Role |
|---|---|
| `qc_scipatent_digest/pipeline.py` | reusable `DigestPipeline`, `PipelineConfig`, `PipelineResult` |
| `qc_scipatent_digest/plus_ultra.py` | orchestrates PLUS ULTRA run |
| `qc_scipatent_digest/oak_gates.py` | release gates for OAK-Source, OAK-IP, OAK-Science |
| `qc_scipatent_digest/entity_resolution.py` | entity clustering and homonym/alias warnings |
| `qc_scipatent_digest/canon_export.py` | DCT++ canon cards export |
| `qc_scipatent_digest/reuse_blueprints.py` | reusable product/service blueprints |
| `schemas/digest_document.schema.json` | normalized document schema |
| `tests/test_plus_ultra.py` | PLUS ULTRA regression test |
| `.github/workflows/qc_scipatent_digest_ci.yml` | CI plan for source-tree mode |

## Validation

```bash
python -m pytest -q
# 2 passed
python -m qc_scipatent_digest.cli plus-ultra --out outputs/plus_ultra_v03
```

## Note

The GitHub PR currently records the scaffold, release notes, architecture and manifests. The runnable full source package is available as the local artifact linked in the ChatGPT response. A follow-up PR can expand the whole source tree into `projects/qc_scipatent_digest/` when desired.
