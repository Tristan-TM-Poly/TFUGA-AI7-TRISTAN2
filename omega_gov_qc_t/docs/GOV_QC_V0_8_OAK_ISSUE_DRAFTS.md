# Ω-GOV-QC-T v0.8 — OAK Issue Drafts

**Status:** C / local workflow prototype  
**Network access:** disabled  
**Remote issue creation:** disabled by default  
**Purpose:** convert generated demo artifacts into review-safe local issue drafts.

---

## 1. Why this exists

v0.6/v0.7 added CLI reports, JSON bundles, GraphML export and CI artifacts.

v0.8 adds the next operational layer:

```text
municipal demo artifacts
→ OAK issue drafts
→ JSON + Markdown review bundle
→ optional human-reviewed project issues later
```

This keeps generation automated while preserving accountable review before any operational use.

---

## 2. OAK boundary

The generated issues are **local drafts**, not published issues.

They are not:

- final findings;
- official decisions;
- enforcement outputs;
- public authority statements;
- automated decisions about people or institutions.

They are:

- review checklists;
- governance tasks;
- source/provenance reminders;
- dataset quality review aids;
- human-review gates;
- graph semantics safeguards.

---

## 3. New module

```text
omega_gov_qc_t/src/omega_gov_qc_t/oak_issue_generator.py
```

Exports:

```python
OAKIssueDraft
OAKIssueBundle
OAKIssueGenerator
```

The bundle can render:

```python
bundle.to_json()
bundle.to_markdown()
```

---

## 4. New CLI commands

```bash
omega-gov-qc issues-json --out reports/generated/oak_issue_drafts.json
omega-gov-qc issues-md --out reports/generated/oak_issue_drafts.md
```

The existing demo command now includes issue draft artifacts:

```bash
omega-gov-qc demo --out reports/generated/omega_gov_qc
```

Outputs:

```text
municipal_demo_report.md
municipal_demo_bundle.json
municipal_demo.graphml
oak_issue_drafts.json
oak_issue_drafts.md
```

---

## 5. Draft issue classes

Current generated drafts:

1. Source authorization before pilot
2. Dataset health baseline before dashboards
3. Human-review gate for high-impact contexts
4. GovGraph / GraphML semantics review

Each draft contains:

```yaml
issue_id: stable local ID
title: review-safe title
body_markdown: checklist and OAK boundary
labels: suggested project labels
priority: P1/P2
issue_type: governance category
source: source object or module
oak_status: review status
```

---

## 6. Review policy

Before converting a draft into a real project issue:

```yaml
required:
  - human review
  - source authorization review
  - privacy/security review where needed
  - removal of sensitive or personal data
  - clear statement that signals are review aids only
```

---

## 7. Next gates

- Add optional remote issue creation only after explicit user confirmation.
- Add project labels bootstrapper.
- Add mapping from real bundle JSON to issue drafts.
- Add snapshot tests for Markdown output.
- Add severity rules from DatasetHealthReport and RiskRegister.
