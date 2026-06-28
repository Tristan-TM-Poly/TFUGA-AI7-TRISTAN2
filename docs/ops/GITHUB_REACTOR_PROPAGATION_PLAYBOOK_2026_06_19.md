# GitHub Reactor Propagation Playbook — 2026-06-19

Status: OAK-safe propagation plan  
Root repo: `Tristan-TM-Poly/TFUGA-AI7-TRISTAN2`  
Operating principle: maximum construction, minimum irreversible action.

## 1. Reactor goal

Turn the Tristan GitHub ecosystem into a set of interoperable, auditable repository nodes:

```text
repo -> role card -> audit -> OAK score -> M_MINUS -> draft PR -> canon decision
```

The goal is not blind automation. The goal is reviewable acceleration.

## 2. Repository roles

| Repo | Reactor role | Priority | First propagation packet |
|---|---|---:|---|
| `TFUGA-AI7-TRISTAN2` | root reactor | P0 | GitHub Reactor kernel + workflow + manifest |
| `Tristan_Tardif-Morency_TFUG` | deep corpus mine | P0 | promote `continuous_audit.py` outputs into common OAK format |
| `Tristan_Tardif-Morency_TFUGAG` | AIT generator package | P1 | package audit + pytest + release-readiness card |
| `PEFA-FractalEnergySystem` | PEFA energy scaffold | P1 | conservation/stability simulation contract |
| `TFACC` | converted canon corpus | P2 | classify converted materials into claims/status registry |
| `TTM-TFUGA-AI7-TRISTAN2` | mirror or variant seed | P2 | define sync/variant policy |

## 3. Standard repo contract

Every repo should eventually contain an equivalent of:

```text
docs/REPO_CANON_ROLE.md
docs/claims.md
schemas/github_reactor_repo.schema.json or root link
memory/m_minus/*.jsonl
reports/autopilot/README.md
.github/workflows/repo-audit.yml
```

## 4. Propagation levels

### Level A — Observation only

Allowed:

- list files;
- compile Python;
- run local tests;
- generate reports;
- upload artifacts.

### Level B — Additive draft PR

Allowed:

- create branch;
- add docs/schemas/reports/scripts;
- open draft PR;
- attach OAK status.

### Level C — Canon promotion

Allowed only after:

- tests pass or failures are recorded as M_MINUS;
- high-risk claims are reviewed;
- OAK status is explicit;
- residue is documented;
- next test is known.

## 5. Blocked behaviors

The reactor must not perform irreversible actions silently. It must not treat a generated report as proof, deployment, official publication, or physical validation.

## 6. Bayes-Tristan priority rule


action_score = information_gain + cvcd_gain + prototype_value - cost - risk - m_minus_penalty

Use this to rank work:

| Action | Score intuition | Verdict |
|---|---|---|
| Add root reactor audit kernel | high information, low risk | done in PR #36 |
| Continue collecting failed tests as artifacts | high repair value | done in PR #36 |
| Propagate repo contract to peer repos | high CVCD coherence | next |
| Add PEFA conservation tests | high proof gain | priority |
| Merge everything without review | high risk | blocked |

## 7. Root PR queue

Current key PRs observed:

- PR #36 — GitHub Autonomous Reactor Audit Packet.
- PR #35 — Canon unification scaffold for TFUGA AI7 AIT.
- PR #34 — Repo canon role.
- PR #21 — Tristan Hypergraphs HGFM OAK-strict canon.

Recommended order:

```text
#36 -> #35 -> #34 -> #21
```

Reason:

1. #36 creates the audit/safety spine.
2. #35 centralizes canon and claims.
3. #34 standardizes repository role.
4. #21 expands the HGFM theory canon under stricter gates.

## 8. M_MINUS integration

Every failed run should become a row in:

```text
memory/m_minus/github_reactor_m_minus_seed.jsonl
```

Fields:

```json
{
  "id": "GHR-MMINUS-XXXX",
  "type": "failure_or_risk_type",
  "repository": "owner/repo",
  "evidence": "what happened",
  "repair_rule": "what should future automation do differently",
  "future_penalty_pattern": "pattern to penalize",
  "status": "ACTIVE_GUARDRAIL"
}
```

## 9. Long-term architecture

```text
GitHub Reactor
  -> repo cards
  -> audit reports
  -> OAK matrix
  -> Bayes-Tristan next actions
  -> M_MINUS memory
  -> HGFM interrepo atlas
  -> branch packets
  -> draft PRs
  -> canon promotion
```

## 10. Ultimate guardrail

```text
Autonomy may accelerate construction.
Only OAK-gated review may promote canon.
```
