# Ω-ABSORB-POLY-PROF-T v0.4

Status: zero-touch research absorption compiler upgrade.

## Purpose

v0.4 turns public ResearchAtoms into structured claim graphs, method graphs, deterministic JSON packets, and downstream opportunity bundles.

```text
ResearchAtom
-> ClaimGraph
-> MethodGraph
-> deterministic JSON export
-> CourseCVCD / ProjectForge / GrantForge / IPGate packets
```

## New modules

- `claim_graph.py`: converts claims into claim/evidence/method/limit/test nodes.
- `method_graph.py`: groups reusable methods across ResearchAtoms and scores reproducibility.
- `json_exports.py`: deterministic JSON and packet digest helpers.
- `research_opportunity_compiler.py`: routes each ResearchAtom into CourseCVCD, ProjectForge, GrantForge, and IPGate.

## Commands

```bash
python examples/omega_absorb_poly_prof_v04_demo.py
python -m pytest tests/test_omega_absorb_poly_prof_v04.py
```

## Zero-touch semantics

- Claims are not truth; they become test nodes.
- Methods are not immediately reusable; they receive reproducibility scores.
- Opportunity bundles are generated automatically from public metadata.
- External actions remain represented as blocked-action/capability packets when needed.

## v0.5 next targets

1. rank opportunity bundles by value/risk/reproducibility;
2. generate professor backlog Markdown reports;
3. add public metadata adapter interface;
4. add ClaimGraph and MethodGraph JSON schemas;
5. integrate v0.4 outputs into ProfessorGraph-Poly.
