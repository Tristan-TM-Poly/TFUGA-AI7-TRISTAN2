# omega_infra_qc_t

OAK-safe InfrastructureGraph Quebec MVP.

## Purpose

Model public, private and mixed infrastructure as a safe, review-first graph:

```text
assets -> dependencies -> evidence -> risks -> maintenance -> resilience -> report -> bundle -> graphml
```

## Safety posture

This package uses demo or authorized data only. It does not fetch live data by default and must not publish sensitive infrastructure details.

## Core objects

- `AssetNode`
- `DependencyEdge`
- `InfraGraph`
- `SourceRecord`
- `EvidenceItem`
- `InfraRiskTensor`
- `OAKSecurityGate`
- `MaintenanceSignal`
- `ResilienceScenario`
- `MarkdownReportFactory`
- `JsonExporter`
- `InfraExportBundle`
- `GraphMLExporter`
- `build_demo_artifacts`

## CLI

```bash
omega-infra-qc demo --out reports/generated/omega_infra_qc
omega-infra-qc report --out reports/generated/infra_qc_demo_report.md
omega-infra-qc bundle --out reports/generated/infra_qc_demo_bundle.json
omega-infra-qc graphml --out reports/generated/infra_qc_demo.graphml
```

## Example use

```python
from omega_infra_qc_t import AssetNode, InfraGraph

graph = InfraGraph()
graph.add_asset(AssetNode(asset_id="asset:demo_bridge", name="Demo Bridge", sector="transport"))
print(graph.quality_report())
```

## Demo artifacts

The demo builder generates:

```text
infra_qc_demo_report.md
infra_qc_demo_bundle.json
infra_qc_demo.graphml
```

These are public-safe fictional/generalized artifacts, not real infrastructure assessments.

## Public-safe GraphML

`GraphMLExporter` redacts review/restricted/critical asset labels by default. Use `public_safe=False` only for authorized internal review contexts.

## OAK rule

```text
No real sensitive infrastructure exposure by default.
No final authority claim.
Human review required for real-world use.
```
