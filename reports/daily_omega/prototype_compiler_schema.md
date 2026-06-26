# Daily Ω PrototypeCompiler Schema

**Status:** v0.1 OAK prototype ladder  
**Source:** compiled `SignalGenome++` objects and EvidenceGraphs  
**Safety:** local-only; no GitHub calls; no external actions; no issue creation; no canon promotion.

---

## Purpose

The PrototypeCompiler asks:

```text
What is the smallest safe prototype that this signal can become?
```

A Daily Ω signal should become one of the following:

```text
1 proof note
1 risk note
1 local dry-run
1 prototype
1 benchmark
1 offer/IP/funding note
or 1 clean M- rejection
```

---

## Pipeline position

```text
signal
-> Source Verification Gate
-> EvidenceGraph
-> SignalGenome++
-> PrototypeCompiler
-> P0/P1/P2/P3/P4 plan
-> OAK/IP/revenue/canon queue
```

---

## Prototype ladder

| Level | Horizon | Purpose | Example artifact |
|---|---:|---|---|
| `P0` | 15 min | Verify source and claim. | `source_note.md` |
| `P1` | 2 h | Create local dry-run stub. | `oakbench_stub.py` |
| `P2` | 1 day | Export reproducible evidence. | `evidence_report.md` + `evidence.json` |
| `P3` | 1 week | Compare against baseline. | `benchmark_result.json` |
| `P4` | 1 month | Select business/IP/funding route. | `offer_or_ip_one_pager.md` |

---

## JSON shape

```json
{
  "briefing_date": "2026-06-24",
  "timezone": "Europe/Paris",
  "plans": [
    {
      "signal_title": "...",
      "prototype_horizon": "2_hour",
      "recommended_start": "P0",
      "can_start": true,
      "blockers": ["claim_support_gap"],
      "steps": [
        {
          "level": "P0",
          "horizon": "15_min",
          "objective": "Verify source and write one OAK falsification note.",
          "artifact": "source_note.md",
          "success_metric": "All central claims have at least one review-ready source or an M- rejection note.",
          "oak_gate": "source_check",
          "allowed_public": true
        }
      ],
      "m_minus": "..."
    }
  ]
}
```

---

## Blockers

Common blockers:

```text
claim_support_gap
source_upgrade_check
private_only_ip_review
agent_safety_dry_run_only
infrastructure_assumption_check
```

Blockers do not always prevent P0. They constrain the allowed scope.

```text
Source blocker -> start at P0.
IP blocker -> private artifacts only.
Agent blocker -> dry-run only, no external action.
Infrastructure blocker -> assumptions must be mapped before claims.
```

---

## CLI usage

```bash
python scripts/daily_omega_prototype.py examples/daily_omega_signals --date 2026-06-24
python scripts/daily_omega_prototype.py examples/daily_omega_signals --date 2026-06-24 --format json
```

---

## OAK rule

```text
No source -> P0 only.
No dry-run -> no P2 claim.
No baseline -> no P3 victory claim.
No IP review -> no public detailed artifact.
No observability -> no agentic production claim.
```

The PrototypeCompiler produces plans, not success claims.
