# Ω-ABSORB-POLY-PROF-T v0.8

Status: zero-touch combined fixture, bridge scoring, source registry, and local artifact generation upgrade.

## Purpose

v0.8 makes the public research absorption pipeline more complete by adding a combined fixture loader, fixture-to-artifact generation, department bridge scoring, collaboration Markdown rendering, and a public metadata source registry.

```text
combined fixture records
-> public ResearchAtoms
-> generated artifact run
-> department bridge score
-> collaboration Markdown
-> source registry
```

## New modules

- `fixture_loader_v08.py`: combines PolyPublie-like and expertise-like fixture records.
- `fixture_artifact_generator.py`: turns fixture records into generated report artifacts and summaries.
- `department_bridge_scoring.py`: scores department bridges from professor genomes and pairing recommendations.
- `collaboration_markdown.py`: renders local Markdown for collaboration plans.
- `public_source_registry.py`: registers allowed public metadata source modes and fields.

## Commands

```bash
python examples/omega_absorb_poly_prof_v08_demo.py
python -m pytest tests/test_omega_absorb_poly_prof_v08.py
```

## OAK boundary

- Fixture records are demo/public metadata.
- Claims remain test seeds, not truth.
- Source registry defines allowed metadata fields.
- External platform actions remain capability boundaries.

## v0.9 next targets

1. add source registry validation for incoming records;
2. add generated collaboration artifact examples;
3. add portfolio-to-roadmap compiler;
4. add department bridge report renderer;
5. add end-to-end v0.3-v0.8 pipeline test.
