# Rosette Hyper-Absorption Engine

Rosette Hyper-Absorption extends the current Fidelity layer into a research pipeline for source-traced science artifacts.

## Command

```bash
rosette-hyper examples/sample_paper.txt --out out_hyper
```

## Outputs

```text
out_hyper/
  hyper_absorption.json
  absorption_ladder.json
  claim_evidence_graph.json
  equation_oak.json
  ip_guardian.json
  fidelity/
    source_refs.json
    fidelity_report.json
    theory_capsule.yaml
```

## Modules

- consensus.py: weighted multi-extractor artifact consensus.
- equation_oak.py: first dimensional OAK templates.
- claim_graph.py: claim-to-evidence and counter-check graph.
- code_forge.py: equation-to-code skeleton and safe ODE translation.
- figure_repro.py: reproduction status planner.
- absorption.py: cognitive absorption ladder.
- memory.py: Rosette memory plus/minus registry.
- ip_guardian.py: copyright, license and patent caution layer.
- bench.py: RosetteBench metrics and OAK honesty.
- hyper_pipeline.py: orchestration command.

## OAK status

This layer is research-usable, not certified. It improves orchestration and auditability, but extraction, equations, claims, code and reproduction still require source-specific validation before certification.
