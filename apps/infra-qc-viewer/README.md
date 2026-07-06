# Infra QC Viewer

Status: static MVP viewer
Date: 2026-07-06

## Purpose

`apps/infra-qc-viewer` is a lightweight static interface for the InfrastructureGraph Quebec demo bundle.

It turns:

```text
infra_qc_demo_bundle.json
```

into visible cards, tables and OAK-safe status panels.

## What it displays

- security gate status ;
- graph summary ;
- assets ;
- dependencies ;
- risk tensors ;
- maintenance signals ;
- resilience scenarios ;
- source and evidence summaries ;
- OAK limits.

## Files

```text
index.html
styles.css
app.js
data/infra_qc_demo_bundle.json
```

## Run locally

From repo root:

```bash
python -m http.server 8080
```

Then open:

```text
http://localhost:8080/apps/infra-qc-viewer/
```

## OAK note

This viewer uses generalized demo data only. It is a demonstration interface, not a final engineering, operational or authority decision.

## Next steps

```text
v0.2: load custom JSON bundle
v0.3: add graph visualization
v0.4: add report export and product CTA
v0.5: migrate to Next.js or Vite if needed
```
