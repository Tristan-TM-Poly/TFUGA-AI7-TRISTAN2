# Daily Ω Dashboard Schema

**Status:** v0.1 reusable dashboard export  
**Source:** compiled `SignalGenome++` objects  
**Safety:** local-only; no GitHub calls; no issue creation; no canon promotion.

---

## Purpose

The Daily Ω dashboard compresses a ranked batch into the smallest useful strategic decision layer:

```text
top signal
+ top prototype
+ top revenue path
+ top IP risk
+ top OAK warning
+ top source to verify
+ top next action
+ top infrastructure risk
+ top agent security risk
```

It is designed for reports, CLI output, future dashboards, and Corp-Jarvis planning.

---

## JSON fields

```json
{
  "top_signal": "...",
  "top_prototype": "...",
  "top_revenue": "...",
  "top_ip_risk": "...",
  "top_oak_warning": "...",
  "top_source_to_verify": "...",
  "top_next_action": "...",
  "top_infrastructure_risk": "...",
  "top_agent_security_risk": "..."
}
```

---

## Field semantics

| Field | Meaning |
|---|---|
| `top_signal` | Highest-ranked signal after scoring. |
| `top_prototype` | Smallest useful P0 prototype from the best signal. |
| `top_revenue` | Highest-ranked signal with a non-empty revenue route. |
| `top_ip_risk` | First ranked signal with IP risk above `low_public_signal`. |
| `top_oak_warning` | Main M- warning from the highest-ranked signal. |
| `top_source_to_verify` | First ranked signal whose source is placeholder, weak, or not fully verified. |
| `top_next_action` | Next action from the highest-ranked signal. |
| `top_infrastructure_risk` | First ranked signal with medium/high infrastructure dependency. |
| `top_agent_security_risk` | First ranked signal with non-`none` agent permission scope. |

---

## CLI usage

```bash
python scripts/daily_omega_dashboard.py examples/daily_omega_signals --date 2026-06-24
python scripts/daily_omega_dashboard.py examples/daily_omega_signals --date 2026-06-24 --format json
```

The CLI reads local signal JSON files and emits either Markdown or JSON.

---

## OAK rules

The dashboard is a compression layer, not a promotion layer.

```text
Dashboard selection does not mean source verification.
Dashboard selection does not mean IP clearance.
Dashboard selection does not mean prototype success.
Dashboard selection does not mean canonization.
```

A signal still requires its `oak_validation_route` checks before publication, issue creation, commercialization, or canon promotion.
