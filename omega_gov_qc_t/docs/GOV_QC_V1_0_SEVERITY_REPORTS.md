# Ω-GOV-QC-T v1.0 — Severity Reports

**Status:** C / local review workflow prototype  
**Network access:** disabled  
**Remote publication:** disabled

This note documents the aggregate severity report added to v1.0.

---

## Flow

```text
ExportBundle JSON
→ OAKSeverityReportBuilder
→ OAKSeverityReport
→ JSON + Markdown local files
```

---

## New module

```text
omega_gov_qc_t/src/omega_gov_qc_t/oak_severity_report.py
```

Exports:

```python
OAKSeverityReport
OAKSeverityReportBuilder
```

---

## CLI commands

```bash
omega-gov-qc severity-json \
  --bundle reports/generated/municipal_demo_bundle.json \
  --out reports/generated/oak_severity_report.json

omega-gov-qc severity-md \
  --bundle reports/generated/municipal_demo_bundle.json \
  --out reports/generated/oak_severity_report.md
```

The demo command now includes:

```text
oak_severity_report.json
oak_severity_report.md
```

---

## Report sections

The report summarizes local workflow priority for:

```text
source_registry
dataset_health
risk_register
```

Each decision includes:

```text
priority
status
oak_note
reasons
```

---

## Boundary

```yaml
local_review_only: true
remote_issue_creation: false
network_access: false
human_review_required_before_operational_use: true
```

The severity report is a workflow triage artifact only.
