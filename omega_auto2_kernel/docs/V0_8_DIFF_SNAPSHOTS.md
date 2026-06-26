# Ω-AUTO²-Kernel v0.8 — Diff Reports + Snapshots

## Objectif

v0.8 ajoute des snapshots canoniques et des rapports de diff Markdown/JSON.

## Modules

- `snapshot.py` : construit un snapshot canonique versionné.
- `diff_report.py` : produit un diff JSON ou Markdown contre une baseline.

## CLI

```bash
auto2 snapshot canonical
auto2 diff canonical
auto2 diff canonical --format json
auto2 diff canonical --against fixtures/v0_7_canonical_snapshot.json
```

## OAK

Les snapshots et diff reports sont des sorties texte locales. Ils ne publient rien, ne modifient rien et n'ajoutent aucune action externe autonome.

## Prochaine étape

v0.9 pourra ajouter un orchestrateur local qui exécute `quality-gate`, `compare`, `snapshot` et `diff` en pipeline unique.
