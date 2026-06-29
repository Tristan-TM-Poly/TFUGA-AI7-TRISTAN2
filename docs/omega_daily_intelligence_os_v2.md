# Ω-DAILY-INTELLIGENCE-OS v2

**Status:** v0.2 SignalGenome++ layer  
**Goal:** compile every daily signal into an auditable, reusable strategic asset.

---

## 1. Core upgrade

Daily Ω is no longer only:

```text
briefing -> War Room -> issue candidate
```

It now becomes:

```text
signal -> SourceLedger -> ClaimGraph -> EvidenceMatrix -> SignalGenome++ -> Dashboard -> reports/issues/canon queue
```

No public issue, canon promotion, or external claim is created automatically.

---

## 2. SignalGenome++ fields

Each compiled signal contains:

```text
final_score
canon_branches
ip_classification
issue_type
supervision_mode
prototype_horizon
revenue_routes
canon_status
M+ / M-
source_ledger
claim_graph
evidence_matrix
prototype_ladder
revenue_physics
next_action
```

This turns a news item into a portable object that can be reused in Markdown reports, JSON dashboards, issue specs, IP review, prototype planning, revenue mapping, and canon promotion.

---

## 3. SourceLedger

Source statuses:

```text
source_placeholder
source_required
source_found
source_verified
```

Rule:

```text
source_required or source_placeholder blocks canon promotion.
```

The system treats `source_required:*` as an explicit OAK lock, not a valid citation.

---

## 4. ClaimGraph

Every signal is separated into:

```text
factual_claim
strategic_inference
oak_risk
falsification_route
business_inference
ip_inference
```

This prevents the system from confusing facts, interpretations, opportunities, and speculative extensions.

---

## 5. EvidenceMatrix

Each signal receives compact evidence scoring:

```text
freshness
source
fit
actionability
ip
revenue
prototype
risk
residue
```

This makes the decision auditable and prevents high-energy ideas from bypassing OAK.

---

## 6. PrototypeLadder

Every signal emits a P0..P4 ladder:

```text
P0_15_min   source/OAK note
P1_2_hour   tiny matrix or benchmark skeleton
P2_1_day    local dry-run with Markdown/JSON evidence
P3_1_week   reusable report, issue spec, or dataset
P4_1_month  service/software/licensing evaluation
```

The first prototype must always be small enough to start safely.

---

## 7. RevenuePhysics

Revenue is classified conservatively:

```text
R0_none
R1_manual_service
R1_grant_path
R2_audit_or_report
R5_internal_tool
R7_license_or_api
```

Revenue route is a test plan, never a promise.

---

## 8. DailyDashboard

The OS produces a 7-field dashboard:

```text
top_signal
top_prototype
top_revenue
top_ip_risk
top_oak_warning
top_source_to_verify
top_next_action
```

This compresses the day into one decision, one prototype, one risk, one source to verify, and one next action.

---

## 9. Batch safety improvement

The batch loader now skips metadata files and non-signal JSON files.

A valid signal file must contain:

```text
title
topic_anchor
why_it_matters
actionable_opportunity
oak_check
sources
next_action
scores
```

Files such as `manifest.json`, `metadata.json`, `index.json`, or incomplete JSON notes are skipped as metadata.

---

## 10. Outputs

Batch reports now include:

```text
Daily Ω Briefing
Daily Ω War Room
Daily Ω Intelligence OS
```

Batch exports now include:

```text
{stem}.md
{stem}.decisions.json
{stem}.genomes.json
```

The return value remains backward-compatible: `write_batch_outputs` still returns `(markdown_path, decisions_json_path)`.

---

## 11. Run examples

```bash
python scripts/daily_omega_signal.py examples/daily_omega_signal_template.json --format json
python scripts/daily_omega_intelligence_os.py examples/daily_omega_signal_template.json --format json
python scripts/daily_omega_batch.py examples/daily_omega_signals --date 2026-06-24 --output reports/daily_omega/generated
python scripts/daily_omega_batch.py examples/daily_omega_signals/2026-06-24 --date 2026-06-24 --output reports/daily_omega/generated
```

---

## 12. OAK rule

```text
No source -> no canon.
No claim separation -> no promotion.
No falsification route -> no prototype.
No IP posture -> no public disclosure.
No M- warning -> no strategic memory.
```
