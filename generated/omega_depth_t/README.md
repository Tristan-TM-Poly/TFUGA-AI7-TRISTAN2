# Artefacts Ω-DEPTH-T∞

Ce répertoire conserve des sorties finies et reproductibles du moteur récursif.

## OAKGate profondeur observée n=9

Le rapport versionné se trouve dans [`oakgate-depth9/oak-report.json`](./oakgate-depth9/oak-report.json).

Le bundle complet peut être régénéré avec :

```bash
omega-depth oakgate-example --output-dir generated/omega_depth_t/oakgate-depth9
```

Il produit `depth-graph.json`, `nodes.jsonl`, `tree.md`, `depth-graph.graphml` et `oak-report.json`.

## 40 racines

Le registre humain se trouve dans [`roots/README.md`](./roots/README.md).

Les contrats individuels sont régénérables avec :

```bash
omega-depth scaffold-all --output-dir generated/omega_depth_t/roots
```

Les sorties générées sont des expériences finies. Le nombre de nœuds et la profondeur observée ne sont pas des plafonds permanents.
