# Ω-GOV-QC-T v1.0 — Severity Policy and Snapshots

**Status:** C / local review workflow prototype  
**Network access:** disabled  
**Remote publication:** disabled by default

v1.0 adds deterministic workflow severity for local OAK issue drafts.

---

## Purpose

```text
ExportBundle JSON
→ OAKIssueBundleMapper
→ OAKIssueSeverityPolicy
→ prioritized local review drafts
→ stable JSON/Markdown shape tests
```

The severity layer is for workflow triage only.

---

## New module

```text
omega_gov_qc_t/src/omega_gov_qc_t/oak_issue_severity.py
```

Exports:

```python
SeverityDecision
OAKIssueSeverityPolicy
severity_json
```

---

## Priority bands

```yaml
P0: blocked until review
P1: review required
P2: review recommended
P3: routine review
```

These priorities do not represent official findings or operational decisions.

---

## Policy inputs

The policy currently reads local, already-exported signals:

```yaml
dataset_health:
  - band
  - missing_ratio
  - duplicate_ratio
  - machine_readable

risk_register:
  - local risk values when exported
  - blocker bands when present

source_registry:
  - source item count
  - basic locator and permission fields when present
```

---

## Mapper upgrade

`OAKIssueBundleMapper` now emits:

```yaml
schema: omega_gov_qc_t.oak_issue_bundle.v1.0
```

and each relevant draft includes:

```text
## Local severity
- Priority
- Status
- Note
- Reasons
```

---

## Snapshot tests

v1.0 adds shape tests for:

- severity JSON keys;
- bundle schema version;
- required Markdown sections;
- OAK note text;
- local priority bands.

---

## OAK boundary

```yaml
network_access: false
remote_issue_creation: false
local_review_only: true
human_review_required_before_operational_use: true
```

The output is still a local review pack. It is not remote publication and not a final public-sector decision.

---

## Next gates

- Add richer severity rules from full RiskRegister exports.
- Add real snapshot files only after output format stabilizes.
- Add optional project-label setup only after explicit confirmation.
- Add optional remote issue creation only after explicit confirmation.
