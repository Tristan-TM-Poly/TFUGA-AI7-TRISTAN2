# Ω-GOV-QC-T v0.9 — Bundle Issue Mapping

**Status:** C / local workflow prototype  
**Network access:** disabled  
**Remote publication:** disabled by default

v0.9 maps a local `ExportBundle` JSON file into an `OAKIssueBundle` review pack.

---

## Flow

```text
ExportBundle JSON
→ OAKIssueBundleMapper
→ OAKIssueBundle
→ JSON or Markdown review pack
```

---

## New modules

```text
omega_gov_qc_t/src/omega_gov_qc_t/oak_issue_bundle_mapper.py
omega_gov_qc_t/src/omega_gov_qc_t/oak_issue_labels.py
```

---

## New CLI commands

```bash
omega-gov-qc issues-from-bundle-json \
  --bundle reports/generated/municipal_demo_bundle.json \
  --out reports/generated/oak_issue_drafts_from_bundle.json

omega-gov-qc issues-from-bundle-md \
  --bundle reports/generated/municipal_demo_bundle.json \
  --out reports/generated/oak_issue_drafts_from_bundle.md

omega-gov-qc labels-json \
  --out reports/generated/oak_issue_labels.json
```

---

## Generated local review drafts

The bundle mapper creates review drafts for:

1. source registry review;
2. dataset health signal review;
3. graph and evidence semantics review;
4. risk register review.

---

## OAK boundary

```yaml
network_access: false
remote_publication: false
local_files_only: true
review_required_before_operational_use: true
```

The generated review pack is a planning artifact. It is not a public-sector decision and not a remote mutation.

---

## Label manifest

`oak_issue_labels.py` defines suggested labels such as:

```text
omega-gov-qc
oak-review
source-governance
dataset-health
human-review
graph
semantic-review
bundle-review
```

These labels are exported locally by `labels-json`. They are not created remotely by this command.

---

## Next gates

- Add Markdown snapshot tests.
- Add severity rules from dataset health and risk register content.
- Add optional remote workflow only after explicit review and confirmation.
