# Ω-DAILY Reuse Kit

**Status:** reusable operating kit v0.2  
**Purpose:** make the Daily Ω Briefing / War Room portable across repositories, projects, agents, and future companies.

---

## 1. What is reusable now

The system can now be reused as a seven-part kit:

```text
1. Briefing scorer
2. Canon router
3. IP/revenue posture classifier
4. Issue-spec factory
5. OAK supervisor
6. JSON signal loader/exporter
7. CLI dry-run reviewer
```

This turns any signal into a reviewable artifact without forcing immediate publication or action.

---

## 2. Reusable flow

```text
Signal JSON
→ BriefingItem
→ score_candidate / rank_items
→ route_item
→ make_issue_spec
→ supervise_issue_spec
→ Markdown or JSON export
→ report / issue / memory / prior-art note
```

The important design rule is that the code remains side-effect free until a human-approved connector or GitHub action is used.

---

## 3. Reuse modes

### Mode A — Personal research

Use Daily Ω to transform papers, patents, and tools into:

```text
paper digestion packet
prior-art note
prototype idea
M- warning
canon candidate
```

### Mode B — GitHub project management

Use Daily Ω to transform promising items into issue specs:

```text
issue title
issue body
labels
OAK risk
canon branches
IP/revenue posture
source list
```

### Mode C — Company / revenue scanner

Use Daily Ω to track:

```text
grant leads
procurement leads
startup/customer signals
licensing paths
service/product ideas
```

### Mode D — Publication / IP shield

Use Daily Ω to avoid accidental disclosure:

```text
external prior art
private Tristan idea
confidential review
publication candidate
open/public note
```

### Mode E — Cross-repository portable review

Use a single JSON signal object to generate consistent review artifacts in any repo:

```text
examples/daily_omega_signal_template.json
→ scripts/daily_omega_signal.py
→ Markdown/JSON decision
→ optional issue spec
```

---

## 4. Minimal code usage

```python
from sage_tristan.daily_omega_briefing import rank_items
from sage_tristan.daily_omega_router import make_issue_spec, route_item
from sage_tristan.daily_omega_supervisor import supervise_issue_spec
from sage_tristan.daily_omega_io import load_item_json, export_decision_json

item = load_item_json("examples/daily_omega_signal_template.json")
route = route_item(item)
issue = make_issue_spec(item)
decision = supervise_issue_spec(item, dry_run=True)
print(export_decision_json(item))
```

No GitHub issue is created by these functions. They return reviewable data.

---

## 5. CLI usage

```bash
python scripts/daily_omega_signal.py examples/daily_omega_signal_template.json
python scripts/daily_omega_signal.py examples/daily_omega_signal_template.json --format json
python scripts/daily_omega_signal.py examples/daily_omega_signal_template.json --create-mode
```

`--create-mode` evaluates the gates as if approval were being considered. It still does not call GitHub.

---

## 6. OAK-safe approval ladder

```text
review_spec       = safe dry-run object
private_note      = keep private, not public
prior_art_note    = external public source record
issue_candidate   = safe candidate after review
create_issue      = only after explicit approval and OAK/IP pass
canon_candidate   = only after repeated value or test
```

---

## 7. Portability contract

A signal is portable if it has:

- title;
- topic anchor;
- signal type;
- why it matters;
- actionable opportunity;
- OAK risk;
- falsification route;
- at least one source;
- next action;
- score fields.

A signal is not ready if it lacks source, action, OAK check, or IP posture.

---

## 8. Disruptive leverage

The reusable kit makes the system valuable beyond a single briefing:

```text
same signal object
→ report
→ GitHub issue
→ prior-art entry
→ M+ / M- memory
→ grant/revenue lead
→ prototype test
→ canon candidate
```

This is the key multiplication effect: one input can create many controlled artifacts.

---

## 9. Next reusable upgrades

1. Private IP notebook exporter.
2. Prior-art manifest updater.
3. Safe GitHub connector bridge with explicit approval.
4. Cross-repository project router.
5. Dashboard of open Daily Ω decisions.
6. Batch mode for folders of signal JSON files.
7. Automatic report writer for `reports/daily_omega/YYYY-MM-DD.md`.

---

## 10. OAK rule

Reusable does not mean automatic. Reusable means the same object can move through many safe paths while preserving source, risk, IP posture, and next action.