# Ω-AUTO²-Kernel v1.0

**Automatisation de l’Automatisation de TRISTAN** — noyau local OAK-safe pour transformer une friction répétée en workflow généré, simulé, validé, benché, snapshoté, comparé, puis préparé comme release candidate sous souveraineté humaine.

> ZÉRO-TOUCH maximal, jamais zéro-contrôle.

## Statut OAK

| Dimension | Statut |
|---|---|
| Nature | Prototype logiciel / architecture de recherche |
| Version | 1.0.0 |
| Niveau | Release candidate local |
| Actions externes | Interdites par défaut |
| Suppression / publication / email / argent | Red locks + verrou humain obligatoire |
| Objectif | Orchestrer AUTO² localement sans effet externe autonome |

## Boucle canonique

```text
Friction → WorkflowSynth → Sandbox → OAKGate → MaxCap → Telemetry → Proof → Bench → Export → Compare → Snapshot → DiffReport → ReleaseCheck → HumanSovereignty → Orchestrator → M⁺/M⁻
```

## Nouveautés v1.0

v1.0 ajoute :

- version `1.0.0`;
- `sovereignty.py` : Human Sovereignty Layer;
- `orchestrator.py` : orchestrateur release-candidate;
- CLI `auto2 orchestrate canonical`;
- red-lock checks;
- fixture `expected_orchestrator_rc.json`;
- tests orchestrator/sovereignty;
- documentation `docs/V1_0_ORCHESTRATOR.md`.

## Commandes CLI

```bash
auto2 version
auto2 forge "créer un workflow GitHub OAK-safe"
auto2 bench canonical --format json
auto2 compare canonical
auto2 snapshot canonical
auto2 diff canonical
auto2 release-check canonical
auto2 orchestrate canonical
auto2 orchestrate canonical --actions local_report dry_run
auto2 orchestrate canonical --actions public_publish
auto2 quality-gate
```

## Red locks

```text
delete_files
public_publish
external_email
spend_money
change_permissions
ip_disclosure
legal_commitment
medical_decision
unsafe_physical_action
```

## Règles rouges

Ce noyau ne doit jamais autoriser automatiquement : suppression sans backup, publication publique sans OAK/IP check, divulgation de secrets, envoi externe sans consentement, transaction financière, boucle récursive non bornée, expérimentation physique dangereuse, décision médicale/légale autonome.

## Roadmap

1. **v0.1** : schéma + OAKGate + friction score + exemples + MaxCap initial.
2. **v0.2** : sandbox/dry-run + CI GitHub Actions.
3. **v0.3** : telemetry + proof-of-workflow + draft improver.
4. **v0.4** : bench suite + markdown reports.
5. **v0.5** : workflows canoniques benchés + exports JSON/Markdown enrichis.
6. **v0.6** : CLI bench canonique + fixtures + changelog + OAK/M⁻ reports.
7. **v0.7** : regression fixtures + score comparisons across versions.
8. **v0.8** : generated diff reports + checked-in canonical benchmark snapshots.
9. **v0.9** : local release pipeline quality-gate + compare + snapshot + diff.
10. **v1.0** : AUTO²-Orchestrator avec Human Sovereignty Layer.
