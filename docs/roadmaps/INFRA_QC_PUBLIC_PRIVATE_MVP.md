# INFRA-QC Public / Private MVP Roadmap

Status: B/C — implementation roadmap
Date: 2026-07-06

## 0. Mission

Build a reusable OAK-safe infrastructure graph MVP for public, private and mixed infrastructure analysis in Quebec.

```text
authorized input -> source registry -> asset graph -> risk tensor
                 -> maintenance signal -> resilience report -> OAK-safe report
```

## 1. MVP v0.1 scope

```text
AssetNode
DependencyEdge
InfraGraph
SourceRecord
EvidenceItem
InfraRiskTensor
OAKSecurityGate
MaintenanceSignal
ResilienceScenario
MarkdownReportFactory
JSON export
schemas
examples
tests
```

## 2. Non-goals

The MVP does not:

- fetch live infrastructure data ;
- publish sensitive asset details ;
- identify exploitable weaknesses ;
- replace engineers, operators, regulators, public authorities or emergency managers ;
- score real communities without authorization and review ;
- expose exact critical dependencies.

## 3. Demo assets

Use only generalized or fictional examples:

```text
municipal water facility demo
local bridge demo
school building demo
generalized data center demo
food warehouse demo
generalized telecom node demo
```

## 4. OAK gates

```yaml
public_data_only_by_default: true
no_sensitive_location_by_default: true
no_exploit_details: true
human_review_for_real_use: true
community_context_required: true
security_review_for_critical_assets: true
```

## 5. Product ladder

```text
v0.1 docs + model + tests
v0.2 CLI + generated reports
v0.3 dashboard skeleton
v0.4 public/private visibility tiers
v0.5 procurement and maintenance prioritizer
v0.6 climate/resilience scenario simulator
```

## 6. Success criteria

- Example graph loads.
- Risk tensors compute bands.
- Security gate blocks sensitive publication contexts.
- Maintenance signals rank priorities.
- Resilience report summarizes scenarios without exposing sensitive details.
- Tests cover core gates.
