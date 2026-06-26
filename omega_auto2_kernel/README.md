# Ω-AUTO²-Kernel v0.9

**Automatisation de l’Automatisation de TRISTAN** — noyau prototype pour transformer une friction répétée en workflow généré, simulé, validé par OAK, mesuré, prouvé, amélioré, benché, exporté, comparé, snapshoté et validé par pipeline local de release.

> ZÉRO-TOUCH maximal, jamais zéro-contrôle.

## Statut OAK

| Dimension | Statut |
|---|---|
| Nature | Prototype logiciel / architecture de recherche |
| Version | 0.9.0 |
| Niveau | Draft contrôlé |
| Actions externes | Interdites par défaut |
| Suppression / publication / email / argent | Verrou humain obligatoire |
| Objectif | Unifier quality-gate, compare, snapshot et diff en un release-check local |

## Boucle canonique

```text
Friction → LOG/CVCD → Workflow DNA → WorkflowSynth → Sandbox/Dry-run → OAKGate → MaxCap → Telemetry → Proof → Bench → Export → Compare → Snapshot → DiffReport → ReleaseCheck → CLI → M⁺/M⁻
```

## Nouveautés v0.9

v0.9 ajoute :

- version `0.9.0`;
- `release.py`;
- CLI `auto2 release-check canonical`;
- sortie release Markdown/JSON;
- fixture `expected_release_pipeline.md`;
- tests release pipeline;
- documentation `docs/V0_9_RELEASE_PIPELINE.md`.

## Commandes CLI

```bash
auto2 version
auto2 forge "créer un workflow GitHub OAK-safe"
auto2 bench canonical --format markdown
auto2 bench canonical --format json
auto2 compare canonical
auto2 snapshot canonical
auto2 diff canonical
auto2 release-check canonical
auto2 release-check canonical --format json
auto2 release-check canonical --against fixtures/v0_7_canonical_snapshot.json
auto2 report canonical
auto2 quality-gate
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
