# Ω-AUTO²-Kernel v0.5 — Canonical Benchmarks

## Objectif

v0.5 ajoute une suite canonique de workflows benchés et des exports JSON/Markdown.

## Workflows canoniques

- `daily_briefing`
- `github_factory`
- `maxcap_assessment`
- `drivebrain_draft`

Ces workflows sont créés par `canonical_workflows()` et peuvent être évalués par `run_suite()`.

## Exports

- `suite_json(workflows)` retourne un rapport JSON lisible.
- `suite_markdown(workflows)` retourne un rapport Markdown.

## Exemple

```python
from omega_auto2 import canonical_workflows, suite_json, suite_markdown

workflows = canonical_workflows()
json_report = suite_json(workflows)
md_report = suite_markdown(workflows)
```

## OAK

Les exports ne publient rien et ne modifient rien. Ils produisent seulement des chaînes de texte locales/draft.

## Prochaine étape

v0.6 pourra ajouter un CLI bench canonique :

```bash
auto2 bench canonical --format markdown
```

et des fixtures de référence pour comparer les scores entre versions.
