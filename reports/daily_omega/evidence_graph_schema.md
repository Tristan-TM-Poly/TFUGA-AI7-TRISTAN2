# Daily Ω EvidenceGraph Schema

**Status:** v0.1 OAK evidence graph  
**Source:** compiled `SignalGenome++` objects  
**Safety:** local-only; no web calls; no GitHub calls; no issue creation; no canon promotion.

---

## Purpose

The Source Verification Gate asks:

```text
Are the sources strong enough to review?
```

The EvidenceGraph asks:

```text
Are the claims, inferences, counter-hypotheses, and blockers structured enough for OAK review?
```

---

## Pipeline position

```text
signal
-> SourceLedger
-> Source Verification Gate
-> ClaimGraph
-> EvidenceGraph
-> CounterHypothesisGraph
-> EvidenceMatrix
-> SignalGenome++
-> OAK/IP/canon queue
```

---

## JSON shape

```json
{
  "briefing_date": "2026-06-24",
  "timezone": "Europe/Paris",
  "is_clear": false,
  "graphs": [
    {
      "signal_title": "...",
      "factual_claims": [
        {
          "claim_type": "factual_claim",
          "text": "...",
          "support_level": "weak",
          "contradiction_level": "medium",
          "source_refs": ["title::identifier"],
          "residue": "source_required"
        }
      ],
      "strategic_inferences": [],
      "counter_hypotheses": [],
      "evidence_score": {
        "source_quality": 0,
        "corroboration": 0,
        "specificity": 0,
        "reproducibility": 0,
        "contradiction_risk": 0
      },
      "promotion_blockers": ["claim_support_gap"]
    }
  ]
}
```

---

## Support levels

| Level | Meaning |
|---|---|
| `none` | No usable source present. |
| `weak` | Placeholder or weak source exists. |
| `medium` | Source exists but needs corroboration. |
| `strong` | Source is review-ready. Still not automatic canon. |

---

## Promotion blockers

Common blockers:

```text
claim_support_gap
source_upgrade_check
ip_check
ip_public_disclosure_block
safety_check
agent_observability_gap
```

A blocker means:

```text
Do not promote to public issue, canon, business-facing claim, or IP route until resolved.
```

---

## Counter-hypotheses

Every graph should contain at least one counter-hypothesis. Examples:

```text
The central factual signal may be unsupported or overstated.
The signal may be attractive but blocked by an unresolved OAK gate.
The public framing may damage IP position or collide with prior art.
The agentic route may fail through unsafe permissions or missing observability.
The opportunity may depend on fragile infrastructure or supply-chain assumptions.
```

---

## CLI usage

```bash
python scripts/daily_omega_evidence.py examples/daily_omega_signals --date 2026-06-24
python scripts/daily_omega_evidence.py examples/daily_omega_signals --date 2026-06-24 --format json
```

---

## OAK rule

```text
No counter-hypothesis -> no canon.
No factual support -> no public claim.
No blocker resolution -> no promotion.
No baseline -> no prototype victory claim.
```
