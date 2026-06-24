# Ω-ST v2 Implementation Backlog

This backlog converts the plus-ultra canon into sequenced implementation work.

## Already added in this PR

- `docs/SCIENCES_DE_TRISTAN_V2_PLUS_ULTRA.md`
- `examples/sciences_tristan_v2_architecture.yaml`
- `examples/sciences_tristan_physics.json`
- `sage_tristan/sciences_tristan/v2_extensions.py`
- `tests/test_sciences_tristan_v2_extensions.py`

## Implemented v2 executable concepts

- `ClaimTransmuter`
- `MemoryMinusEngine`
- `PromotionGates`
- `CanonScore`
- `OAKCourt`
- `ResidueMiner`
- `ScienceOrganism`
- `portfolio_dashboard`

## Next PR sequence

1. Add command-line wrappers for v2 audit, gates, transmute and dashboard.
2. Add GitHub Actions CI for the Sciences de Tristan test subset.
3. Add JSON schema for `ScienceOrganism`.
4. Add JSON schema for `OAKCourtReview`.
5. Add Fractal RLC Lab scaffold.
6. Add FFWT-HAC-CVCD benchmark scaffold.
7. Add PaperForge manuscript-seed generator.
8. Add HGFM edge-typing module.
9. Add DimensionCheck for physics equations.
10. Add AblationEngine.
11. Add TheoryGenome model.
12. Add ExperimentContract and PrototypeContract schemas.

## Testing targets

- high fertility is not high truth;
- high priority is not high canon;
- physics/material claims require measurement checks;
- theorem language requires definitions and assumptions;
- exotic algebra requires real projection and ablation;
- agents require benchmarks;
- residues can generate child hypotheses;
- promotion requires OAK gates.

## Zero-touch target pipeline

```text
idea.md -> science_card.json -> transmutation.json -> oak_court_review.json
        -> prototype_contract.yaml -> experiment_contract.yaml
        -> benchmark_report.json -> residue_cards.json
        -> canon_update.md -> paper_seed.md
```
