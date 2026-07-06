# omega_infra_qc_t

OAK-safe InfrastructureGraph Quebec MVP.

## Purpose

Model public, private and mixed infrastructure as a safe, review-first graph:

```text
assets -> dependencies -> evidence -> risks -> maintenance -> resilience -> report
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

## Example use

```python
from omega_infra_qc_t import AssetNode, InfraGraph

graph = InfraGraph()
graph.add_asset(AssetNode(asset_id="asset:demo_bridge", name="Demo Bridge", sector="transport"))
print(graph.quality_report())
```

## OAK rule

```text
No real sensitive infrastructure exposure by default.
No final authority claim.
Human review required for real-world use.
```
