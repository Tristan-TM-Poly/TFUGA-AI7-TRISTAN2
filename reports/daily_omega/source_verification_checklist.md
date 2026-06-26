# Daily Ω Source Verification Checklist

**Status:** v0.1 OAK source gate  
**Scope:** compiled `SignalGenome++` objects  
**Safety:** local-only; no web calls; no GitHub calls; no issue creation; no canon promotion.

---

## Purpose

Before a signal becomes a public issue, canon candidate, product idea, customer-facing claim, or IP route, Daily Ω must verify that its sources are strong enough.

This checklist detects:

```text
source_placeholder
source_required
source_found
```

and converts them into explicit verification actions.

---

## CLI usage

```bash
python scripts/daily_omega_verify.py examples/daily_omega_signals --date 2026-06-24
python scripts/daily_omega_verify.py examples/daily_omega_signals --date 2026-06-24 --format json
```

---

## Verification states

| Status | Meaning | Blocking? | Next action |
|---|---|---:|---|
| `source_placeholder` | Placeholder such as `source_required:*`. | Yes | Replace with primary or credible secondary source. |
| `source_required` | Source quality too low. | Yes | Find a stronger source and corroborate. |
| `source_found` | Source exists but is not fully promotion-ready. | No | Corroborate with another credible source or artifact. |
| `source_verified` | Source is review-ready. | No | Continue OAK review; still not automatic canon. |

---

## Promotion rule

```text
No source verification -> no canon promotion.
No source verification -> no public technical issue.
No source verification -> no business-facing claim.
No source verification -> no patent/publication inference.
```

---

## OAK-safe interpretation

The verifier does not prove that a claim is true.

It only answers:

```text
Which signals still need source work before promotion?
What is the blocking source gap?
What is the next source check?
```

The full OAK route still requires claim separation, falsification, IP review, safety review, observability, infrastructure mapping, and prototype validation.
