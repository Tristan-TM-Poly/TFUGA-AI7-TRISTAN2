# Ω-SCI-PATENT-QC-DIGEST-T — PLUS ULTRA artifact ledger

## Git policy

- Default destination: Tristan Git/GitHub.
- Branch: `omega-scipatent-qc-digest-max`.
- Repository: `Tristan-TM-Poly/TFUGA-AI7-TRISTAN2`.
- Path namespace: `projects/qc_scipatent_digest/`.
- Merge policy: PR draft first; no automatic merge into `main`.

## Local package artifacts

### MAX package

- `qc_scipatent_digest_max.zip`
- SHA-256: `a909ddf08232583d19397aa577754f40e67e5e7a3a570b9e821d6298a069d64c`

### PLUS ULTRA v0.3 package

- `qc_scipatent_digest_plus_ultra.zip`
- SHA-256: `e48aed805f9aa62d6c665ef137189aeeb1bac2504bd6c27185146636e93749ff`

## Local validation

```bash
python -m pytest -q
# 2 passed

python -m qc_scipatent_digest.cli plus-ultra --out outputs/plus_ultra_v03
# Documents: 6 | Opportunities: 6 | Bridges: 9
```

## PLUS ULTRA outputs

- `outputs/plus_ultra_v03/pipeline_summary.json`
- `outputs/plus_ultra_v03/release_assessment.md`
- `outputs/plus_ultra_v03/reuse_blueprints.md`
- `outputs/plus_ultra_v03/canon_pack/dct_cards.md`
- `outputs/plus_ultra_v03/entity_clusters.json`
- `outputs/plus_ultra_v03/entity_resolution_warnings.md`
- plus all MAX outputs: dashboard, SQLite, bridges, review queue, hypergraph, opportunities.

## OAK warning

Do not publish or commercialize opportunities from this digest without OAK-IP review:

1. verify publication metadata and affiliation disambiguation;
2. verify patent family, claims, owner, legal status, territory and dates;
3. classify each asset as open, publishable, patentable, trade secret, licensed, blocked or unknown;
4. avoid disclosing potentially patentable inventions before IP review.
