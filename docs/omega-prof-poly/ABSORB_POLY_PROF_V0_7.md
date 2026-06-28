# Ω-ABSORB-POLY-PROF-T v0.7

Status: zero-touch generated artifacts, fixtures, enriched graph export, and cross-domain pairing upgrade.

## Purpose

v0.7 persists deterministic demo artifacts, adds public metadata fixtures, enriches GraphML export, adds artifact summaries, and introduces a cross-domain pairing recommender.

```text
public/demo records
-> ResearchAtoms
-> reports
-> artifact summary
-> enriched ProfessorGraph GraphML
-> cross-domain pairing plan
```

## New modules

- `artifact_summaries.py`: deterministic summaries for generated artifacts.
- `collaboration_recommender.py`: cross-department pairing recommendations from ProfessorResearchGenome objects.
- `enriched_graph_exports.py`: GraphML with node/edge metadata keys.

## New fixtures and generated artifacts

- `examples/fixtures/polypublie_like_records_v07.json`
- `examples/fixtures/expertise_like_records_v07.json`
- `generated/omega_absorb_poly_prof_v07/README.md`
- `generated/omega_absorb_poly_prof_v07/artifact_index.json`
- `generated/omega_absorb_poly_prof_v07/professor_demo_backlog.md`
- `generated/omega_absorb_poly_prof_v07/collaboration_seed.md`

## Commands

```bash
python examples/omega_absorb_poly_prof_v07_demo.py
python -m pytest tests/test_omega_absorb_poly_prof_v07.py
```

## OAK boundary

- Fixtures use demo public metadata only.
- Claims are converted into test seeds, not treated as truth.
- Generated artifacts are examples, not institutional decisions.
- External publishing or platform actions remain capability boundaries.

## v0.8 next targets

1. add combined fixture loader;
2. generate actual artifacts from fixture loader in tests;
3. add department bridge scoring;
4. add collaboration backlog Markdown renderer;
5. add public metadata source registry.
