# VersionForge-T — Ω-GAME-T+++

`VersionForge-T` transforme un `FeedbackLoopResult` en plan de version OAK-safe.

Il prolonge la chaîne :

```text
Theory -> Product -> RevenuePlan -> FeedbackLoop -> VersionForge -> VersionPlan -> Better Product
```

## Rôle

VersionForge lit la décision de feedback, M+ et M-, puis produit : version cible, changelog, priorités, critères de release, blockers OAK et prochaines tâches.

Il ne publie pas de release, ne tague pas Git, ne modifie pas de dépôt externe et ne lance aucune action automatique.

## Entrée

```yaml
feedback_loop:
  confidence_score: 0.64
  decision: build_targeted_mini_demo
  next_version: v0.2-targeted-mini-demo
  m_plus:
    - concrete_use_case_found
  m_minus:
    - pricing_not_validated
```

## Sortie

```yaml
version_plan:
  version: v0.2-targeted-mini-demo
  release_type: internal_iteration
  priorities:
    - amplify concrete_use_case_found
    - reduce pricing_not_validated
  release_criteria:
    - tests pass
    - OAK controls visible
    - M+/M- recorded
```

## Règles OAK

- Un plan de version n'est pas une release publique.
- Une version interne ne doit pas être taguée publiquement sans revue.
- M+ sert à amplifier ce qui marche.
- M- sert à empêcher la répétition des erreurs.
- Les critères OAK doivent bloquer toute release ambiguë.

## Décisions MVP

| Décision FeedbackLoop | Version |
|---|---|
| `prepare_reviewed_private_pilot` | `v0.3-reviewed-private-pilot` |
| `build_targeted_mini_demo` | `v0.2-targeted-mini-demo` |
| `improve_pitch_and_clarity` | `v0.1-clarity-pass` |
| `rework_value_proposition` | `v0.1-rework` |

## Extension prévue

- génération de changelog Markdown ;
- export vers IssueForge ;
- release checklist ;
- version diff ;
- semantic version policy ;
- GitHub tag/release après approbation humaine.
