# Ω-DAILY Reuse Kit

**Status:** reusable operating kit v0.1  
**Purpose:** make the Daily Ω Briefing / War Room portable across repositories, projects, agents, and future companies.

---

## 1. What is reusable now

The system can now be reused as a five-part kit:

```text
1. Briefing scorer
2. Canon router
3. IP/revenue posture classifier
4. Issue-spec factory
5. OAK supervisor
```

This turns any signal into a reviewable artifact without forcing immediate publication or action.

---

## 2. Reusable flow

```text
Signal
→ BriefingItem
→ score_candidate / rank_items
→ route_item
→ make_issue_spec
→ supervise_issue_spec
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

---

## 4. Minimal code usage

```python
from sage_tristan.daily_omega_briefing import rank_items
from sage_tristan.daily_omega_router import make_issue_spec, route_item
from sage_tristan.daily_omega_supervisor import supervise_issue_spec

ranked = rank_items(items)
for item in ranked:
    route = route_item(item)
    issue = make_issue_spec(item)
    decision = supervise_issue_spec(item, dry_run=True)
```

No GitHub issue is created by these functions. They return reviewable data.

---

## 5. OAK-safe approval ladder

```text
review_spec       = safe dry-run object
private_note      = keep private, not public
prior_art_note    = external public source record
issue_candidate   = safe candidate after review
create_issue      = only after explicit approval and OAK/IP pass
canon_candidate   = only after repeated value or test
```

---

## 6. Portability contract

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

## 7. Disruptive leverage

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

## 8. Next reusable upgrades

1. JSON loader for signal files.
2. Markdown exporter for issue specs.
3. Private IP notebook exporter.
4. Prior-art manifest updater.
5. Safe GitHub connector bridge with explicit approval.
6. Cross-repository project router.
7. Dashboard of open Daily Ω decisions.

---

## 9. OAK rule

Reusable does not mean automatic. Reusable means the same object can move through many safe paths while preserving source, risk, IP posture, and next action.