# Ω-AUTO²-Kernel v0.7 — Regression Benchmarks

## Objectif

v0.7 empêche une nouvelle version de régresser silencieusement.

## Modules

- `score_compare.py` : compare un benchmark courant à une baseline.
- `regression.py` : construit la suite canonique courante et lance le check anti-régression.

## CLI

```bash
auto2 compare canonical
auto2 compare canonical --against fixtures/v0_6_canonical_bench.json
```

## Politique OAK

Une version passe si :

- le nombre de workflows canoniques est conservé ou augmenté;
- le pass rate est conservé ou augmenté;
- les exports JSON/Markdown restent disponibles;
- aucune action externe autonome n'est ajoutée.

## Prochaine étape

v0.8 pourra ajouter une vraie baseline générée automatiquement depuis la CI et un rapport de diff Markdown.
