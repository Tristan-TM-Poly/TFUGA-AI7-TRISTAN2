# Ω-SUMMARY-FRACTAL-T∞ — Architecture

## Pipeline

```text
checkout -> RepositoryScanner -> SHA-256 evidence inventory -> system resolver -> optional Python AST -> SummaryHypergraph -> D0..D9 projection -> audience/focus projection -> structural OAK audit -> gap detector -> duplicate candidates -> deterministic renderer -> Markdown + JSON + operational views
```

## Modules

| Module | Rôle |
|---|---|
| `models.py` | contrats dataclass et sérialisation |
| `scanner.py` | inventaire, hashes, systèmes, AST |
| `graph.py` | relations CONTAINS, focus et zoom |
| `audit.py` | santé, lacunes et doublons heuristiques |
| `summarizer.py` | projections profondeur/audience/focus |
| `render.py` | Markdown, JSON, STATUS/OAK/NEXT_ACTIONS |
| `cli.py` | generate, all-depths, audit |

## Hiérarchie d'autorité

`observed < documented < implemented < tested` décrit uniquement l'état logiciel observable, jamais une hiérarchie de vérité scientifique.

## Sécurité supply-chain

Le workflow utilise `permissions: contents: read`, épingle les actions par SHA, ne fusionne/publie rien, produit les résumés dans CI et compare deux exécutions déterministes.

## Complexité

Inventaire/hash O(B), classification O(F), AST linéaire dans les sources analysées, gap scan O(S), déduplication naïve O(S²). La déduplication devra passer à un index plus efficace lorsque le corpus devient très grand.

## Extension cross-repo

La prochaine couche scanne plusieurs checkouts et ajoute `IMPLEMENTS`, `DEPENDS_ON`, `TESTS`, `SUPPORTS`, `CONTRADICTS`, `SUPERSEDES`, `GENERATED_FROM` sans confondre frontière Git et frontière conceptuelle Ω.
