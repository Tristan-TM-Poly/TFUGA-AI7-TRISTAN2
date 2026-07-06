# INFRA-QC v0.2 — CLI / CI / Export Roadmap

Status: C — executable MVP layer
Date: 2026-07-06

## 0. Goal

Turn Ω-INFRA-QC-T from a model package into an executable MVP with deterministic demo artifacts.

## 1. Additions

```text
JsonExporter
InfraExportBundle
build_demo_artifacts
InfraDemoArtifacts
CLI omega-infra-qc
GitHub Actions workflow
CLI/demo/export tests
```

## 2. Commands

```bash
omega-infra-qc demo --out reports/generated/omega_infra_qc
omega-infra-qc report --out reports/generated/infra_qc_demo_report.md
omega-infra-qc bundle --out reports/generated/infra_qc_demo_bundle.json
```

## 3. Generated artifacts

```text
infra_qc_demo_report.md
infra_qc_demo_bundle.json
```

## 4. CI workflow

```text
.github/workflows/omega_infra_qc_tests.yml
```

Workflow steps:

```text
install package
run pytest omega_infra_qc_t
generate demo artifacts
upload omega-infra-qc-demo-artifacts
```

## 5. OAK limits

- generated data is fictional/generalized ;
- bundle is public-safe by default ;
- sensitive details are redacted or omitted ;
- output is review support, not final authority.

## 6. Next strike

```text
v0.3 GraphML export + report snapshots + public/private visibility policy tests
```
