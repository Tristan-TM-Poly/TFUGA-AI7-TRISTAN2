# Ω-AUTO²-Kernel v0.6

**Automatisation de l’Automatisation de TRISTAN** — noyau prototype pour transformer une friction répétée en workflow généré, simulé, validé par OAK, mesuré, prouvé, amélioré, benché, exporté et commandable par CLI.

> ZÉRO-TOUCH maximal, jamais zéro-contrôle.

## Statut OAK

| Dimension | Statut |
|---|---|
| Nature | Prototype logiciel / architecture de recherche |
| Version | 0.6.0 |
| Niveau | Draft contrôlé |
| Actions externes | Interdites par défaut |
| Suppression / publication / email / argent | Verrou humain obligatoire |
| Objectif | Générer, prévisualiser, mesurer, benchmarker, exporter et piloter des workflows OAK-safe |

## Boucle canonique

```text
Friction → LOG/CVCD → Workflow DNA → WorkflowSynth → Sandbox/Dry-run → OAKGate → MaxCap → Telemetry → Proof → Bench → Export → Report → ImproveDraft → CLI → M⁺/M⁻
```

## Nouveautés v0.6

v0.6 ajoute :

- version `0.6.0` dans `pyproject.toml`;
- `omega_auto2.__version__`;
- CLI canonique `auto2`;
- `CHANGELOG.md`;
- `OAK_REPORT.md`;
- `M_MINUS_REPORT.md`;
- fixtures de référence;
- tests CLI.

## Commandes CLI

```bash
auto2 version
auto2 forge "créer un workflow GitHub OAK-safe"
auto2 bench canonical --format markdown
auto2 bench canonical --format json
auto2 report canonical
auto2 quality-gate
```

## Workflows canoniques

```text
daily_briefing
github_factory
maxcap_assessment
drivebrain_draft
```

## Installation locale

```bash
cd omega_auto2_kernel
python -m pip install -e .
pytest
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
8. **v1.0** : AUTO²-Orchestrator avec Human Sovereignty Layer.
