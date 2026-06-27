# Ω-AUTO²-Kernel v1.1

**AUTO-GENESIS v0.1** — extension locale OAK-safe qui transforme une intention en arbre Genesis, idées classées, plan prototype, rapport OAK, chemins de valeur, plan GitHub, M⁺/M⁻ et prochaine action.

> ZÉRO-TOUCH maximal, jamais zéro-contrôle.

## Statut OAK

| Dimension | Statut |
|---|---|
| Nature | Prototype logiciel / architecture de recherche |
| Version | 1.1.0 |
| Niveau | Draft local |
| Actions externes | Interdites par défaut |
| Objectif | Générer des rapports Genesis locaux et actionnables |

## Boucle canonique

```text
Intention → GenesisTree → Ideas → GenesisScore → OAK → PrototypePlan → GitHubPlan → M⁺/M⁻ → NextAction
```

## Nouveautés v1.1

v1.1 ajoute :

- `genesis.py`;
- `genesis_tree.py`;
- `genesis_score.py`;
- `genesis_report.py`;
- CLI `auto2 genesis`;
- fixture `expected_genesis_report.json`;
- tests Genesis;
- documentation `docs/V1_1_AUTO_GENESIS.md`.

## Commandes CLI

```bash
auto2 version
auto2 forge "préparer un paquet de revue local"
auto2 task-draft "préparer un paquet de revue local"
auto2 task-draft "préparer un paquet de revue local" --format json
auto2 task-draft "préparer un paquet de revue local" --output reports/task_draft.md
auto2 genesis
auto2 genesis "créer un moteur de revenus"
auto2 genesis "créer un protocole HEAL" --mode max
auto2 orchestrate canonical
auto2 release-check canonical
auto2 quality-gate
```

## Task drafts

`auto2 task-draft` prépare un brouillon local avec workflow, rapport OAK, labels suggérés, warnings et M⁻. Il ne crée rien dans un système externe. Il est conçu pour alimenter un humain ou un agent approuvé plus tard.

## CI

- `.github/workflows/omega_auto2_ci.yml` teste le package et les commandes CLI principales.
- `.github/workflows/deeptech_forge_ci.yml` teste la DeepTech Forge et les review packets.

## OAK

AUTO-GENESIS et les task drafts produisent seulement des rapports locaux/draft. Toute action externe reste hors module et soumise à la souveraineté humaine.

## Roadmap

1. **v1.0** : AUTO²-Orchestrator avec Human Sovereignty Layer.
2. **v1.1** : AUTO-GENESIS v0.1.
3. **v1.2** : Genesis bundle Markdown/JSON et modes spécialisés.
4. **v1.3** : Task drafts reliés à un registre d'approbation OAK.
