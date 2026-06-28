# Ω-PROF-POLY-T v0.2 — Executable Core

Status: zero-touch executable prototype.

## Core rule

```text
Zero-touch by default.
OAK is an automated compiler.
```

## New modules

- `zero_touch_oak.py`: compiles artifacts into score, status, warnings, next action, and blocked-action packet.
- `coursecvcd.py`: turns course goals into concept graph, exercises, project seeds, rubric axes, and OAK packet.
- `lab_oakbench.py`: turns lab hypotheses into protocol steps, uncertainty sources, coherence tests, and OAK packet.
- `project_forge.py`: creates inter-engineering project packets with deliverables, tests, risks, publication/IP/startup potential, and OAK packet.
- `grant_forge.py`: creates grant packet sections and a grant score.
- `ip_oak_gate.py`: routes results toward publish, patent candidate, open source, trade secret, license candidate, or hold for evidence.
- `professor_graph.py`: lightweight ProfessorGraph-Poly hypergraph.
- `reports.py`: Markdown report renderer.

## Commands

```bash
python examples/omega_prof_poly_v02_demo.py
python -m pytest tests/test_omega_prof_poly_v02.py
```

## Status semantics

- `safe_execute`: generate artifact, tests, and report inside the workspace.
- `auto_generate_only`: generate artifact and OAK report, but keep external action locked.
- `external_action_locked`: artifact ready; execution requires a capability outside the runtime.
- `blocked`: risk threshold exceeded; emit blocked-action packet.

## Next branch

v0.3 should add:

- JSON schema v2 for zero-touch packets;
- report exporters;
- ProfessorGraph import/export;
- deterministic example reports;
- root README integration.
