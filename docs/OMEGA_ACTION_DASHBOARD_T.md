# Ω-ACTION-DASHBOARD-T — Tableau de bord d’action auto-accélérant

## Mission

Ω-ACTION-DASHBOARD-T transforme les boucles d’action de Tristan en tableau de bord opérationnel : GitHub, universités, Gmail, proof packets, assets, M+/M−, capital de preuve, friction brûlée, risques OAK et prochaine meilleure action.

Le dashboard ne sert pas seulement à voir. Il sert à décider.

```text
Observe → Measure → Rank → Act → Verify → Learn → Upgrade
```

## Principe central

```text
Ce qui n’est pas mesuré ne peut pas devenir une boucle auto-accélérante.
```

## Métriques mères

| Métrique | Rôle |
|---|---|
| Proof Capital | somme des preuves réutilisables |
| Friction Burn Rate | frictions supprimées par cycle/semaine |
| OAK Safety Ratio | proportion d’actions sûres |
| Loop Upgrade Rate | actions qui améliorent les futures actions |
| Next Best Action Score | priorité actionnable actuelle |
| Asset Conversion Rate | résultats transformés en actifs |

## Dashboard sections

```yaml
sections:
  Executive_State:
    - active_loops
    - current_blockers
    - next_best_actions
    - proof_capital_delta
  GitHub:
    - open_PRs
    - mergeable_clean_PRs
    - drafts
    - pending_checks
    - repaired_blockers
  Universities:
    - GREEN_EMAIL
    - GREEN_FORM
    - YELLOW_RESEARCH
    - RED_REJECTED
    - replies
    - followup_windows
  ProofPackets:
    - ready_packets
    - seed_packets
    - missing_examples
    - routed_targets
  Assets:
    - code_assets
    - docs_assets
    - packets
    - reports
    - route_assets
    - IP_review_packets
  MPlus_MMinus:
    - success_patterns
    - failure_patterns
    - anti_repetition_rules
  ExternalActionGovernor:
    - internal_auto
    - external_prepared
    - external_approved
    - external_executed
```

## Dashboard rule

Every cycle should answer:

```text
What changed?
What proof was created?
What friction was removed?
What risk was reduced?
What is the next best action?
```

## OAK constraints

The dashboard must not reward unsafe velocity. It must reward safe proof accumulation.

High speed with low proof is not success.

```text
Success = useful action + proof + safety + learning + next action easier than before.
```
