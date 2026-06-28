# Omega Absorb Poly Prof v0.9

Status: zero-touch validation, roadmap and end-to-end pipeline upgrade.

## Purpose

v0.9 adds validation for incoming public records, portfolio-to-roadmap compilation, department bridge reports, generated examples and an end-to-end local pipeline.

```text
fixture records
-> source validation
-> absorption
-> opportunity ranking
-> portfolio selection
-> roadmap
-> department bridge report
-> generated artifacts
-> e2e result
```

## New modules

- `source_record_validation.py`: validates record fields against the public source registry.
- `roadmap_compiler.py`: converts selected portfolio items into roadmap steps.
- `department_bridge_report.py`: renders department bridge scores as Markdown.
- `e2e_pipeline_v09.py`: runs the local v0.3 through v0.9 pipeline.

## Generated examples

- `generated/omega_absorb_poly_prof_v09/README.md`
- `generated/omega_absorb_poly_prof_v09/department_bridge_report.md`
- `generated/omega_absorb_poly_prof_v09/roadmap.md`
- `generated/omega_absorb_poly_prof_v09/e2e_summary.json`

## Commands

```bash
python examples/omega_absorb_poly_prof_v09_demo.py
python -m pytest tests/test_omega_absorb_poly_prof_v09.py
```

## OAK boundary

- Public/demo metadata only.
- Claims remain test seeds.
- Source validation checks fields and routes findings.
- Roadmaps are local plans, not external commitments.

## v1.0 next targets

1. add a stable CLI entry point;
2. add full generated report bundle;
3. add version manifest across v0.3-v0.9;
4. add package-level smoke test;
5. prepare Omega absorb v1.0 release notes.
