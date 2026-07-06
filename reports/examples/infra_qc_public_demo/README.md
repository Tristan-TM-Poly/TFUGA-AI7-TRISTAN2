# InfrastructureGraph Quebec — Public Demo Pack

Status: public-safe demo artifact
Date: 2026-07-06

## Purpose

This folder contains a public-safe demonstration of **Ω-INFRA-QC-T / InfrastructureGraph Quebec**.

It shows how the MVP can transform generalized infrastructure assets into:

```text
asset graph -> source registry -> evidence -> risk tensors -> maintenance signals -> resilience scenarios -> report -> JSON bundle -> GraphML
```

## Files

```text
infra_qc_demo_report.md
infra_qc_demo_bundle.json
infra_qc_demo.graphml
```

## OAK safety note

This demo uses fictional/generalized data only.

It does not contain:

- real sensitive asset locations ;
- operational details ;
- security configurations ;
- emergency plans ;
- personal data ;
- final engineering or authority decisions.

## What this proves

```text
Ω-INFRA-QC-T is not only a concept.
It can generate public-safe infrastructure reports, JSON bundles and GraphML graph exports.
```

## Commands

```bash
omega-infra-qc demo --out reports/generated/omega_infra_qc
omega-infra-qc report --out reports/generated/infra_qc_demo_report.md
omega-infra-qc bundle --out reports/generated/infra_qc_demo_bundle.json
omega-infra-qc graphml --out reports/generated/infra_qc_demo.graphml
```

## Next product path

```text
Infra-OAK Audit Express
-> public-safe infrastructure audit
-> source/evidence/risk/maintenance/resilience report
-> productized service
-> company path
```
