# INFRA-QC Viewer Roadmap

Status: C — static viewer MVP
Date: 2026-07-06

## 0. Goal

Turn the InfrastructureGraph Quebec public demo bundle into a visible interface.

```text
JSON bundle -> cards -> tables -> OAK status -> product CTA
```

## 1. Current MVP

```text
apps/infra-qc-viewer/index.html
apps/infra-qc-viewer/styles.css
apps/infra-qc-viewer/app.js
apps/infra-qc-viewer/data/infra_qc_demo_bundle.json
```

## 2. What it shows

```text
security gate
asset count
dependency count
public-safe status
asset table
risk cards
maintenance signals
resilience scenarios
source registry
evidence items
OAK limits
```

## 3. Why it matters

The previous layer produced files. This layer makes the system visible in 30 seconds.

```text
report -> interface
prototype -> product demo
repo -> client-facing artifact
```

## 4. OAK limits

```text
static demo only
generalized data only
not a final decision
not a real-time system
not a replacement for qualified review
```

## 5. Next strikes

```text
v0.2 load custom JSON bundle
v0.3 graph visualization canvas
v0.4 sample audit generator
v0.5 deployable public site component
```
