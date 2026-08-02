# Ω-PARTICULES-CHAMPS-T∞

Executable R0.2 crystallization of the particle-field hypergraph, identity tensor, OAK gates, QED reference circuit, FFWT residual analysis, Cayley-Dickson hazard audit, and adaptive no-fixed-item-ceiling frontier.

## Run

```bash
python -m pytest tests/test_omega_pct_*.py
python -m omega_pct_t catalog data/omega_pct_catalog.json --json
python -m omega_pct_t qed-reference data/omega_pct_catalog.json --output-dir generated/omega_pct_t/qed-reference --count 256 --sqrt-s 10
python -m omega_pct_t hypercomplex-audit --dimension 16
python -m omega_pct_t frontier --max-seconds 2 --initial-batch 256 --output generated/omega_pct_t/frontier/candidates.jsonl
```

## Scientific boundary

The package mixes established baselines, effective models, and exploratory Tristan infrastructure only when every object carries an explicit status. The synthetic frontier generates research objects for capacity testing; it does not generate discovered particles.

See `docs/OMEGA_PCT_CANON_R0_2.md` and `docs/OMEGA_PCT_FRONTIER_100K_PLUS.md`.
