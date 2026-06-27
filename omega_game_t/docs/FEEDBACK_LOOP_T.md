# FeedbackLoop-T — Ω-GAME-T+++

`FeedbackLoop-T` transforme les signaux privés en mémoire M+ / M-, décisions d'itération et prochaines versions produit.

Il prolonge la chaîne :

```text
Theory -> Product -> LaunchDraft -> RevenuePlan -> FeedbackLoop -> M+/M- -> NextVersion
```

## Rôle

FeedbackLoop lit les signaux de feedback, les classe, calcule un score de confiance, extrait les apprentissages positifs et négatifs, puis propose une prochaine action d'itération.

Il ne contacte personne, ne vend rien, ne publie rien et ne crée aucune action externe.

## Entrée

```yaml
revenue_plan:
  product_name: CircuitDungeon-T Lesson Pack
  success_signals:
    - price_question
    - pilot_request

feedback:
  - signal_type: use_case
    strength: medium
    evidence: reviewer says they could use it in class
```

## Sortie

```yaml
feedback_loop:
  confidence_score: 0.62
  decision: build_targeted_mini_demo
  m_plus:
    - classroom_use_case_found
  m_minus:
    - pricing_not_validated
  next_version: v0.2-targeted-demo
```

## Règles OAK

- Un feedback n'est pas une preuve de marché.
- Un intérêt n'est pas un achat.
- Une question de prix n'est pas un revenu.
- Une demande pilote doit rester revue et cadrée.
- Toute action externe reste bloquée jusqu'à revue humaine.

## Décisions MVP

| Confiance | Décision |
|---|---|
| `>= 0.75` | prepare_reviewed_private_pilot |
| `>= 0.55` | build_targeted_mini_demo |
| `>= 0.35` | improve_pitch_and_clarity |
| `< 0.35` | rework_value_proposition |

## Extension prévue

- intégration directe avec MPlusMemory / MMinusMemory ;
- comparaison de versions ;
- FeedbackBench ;
- export vers IssueForge ;
- boucle ProductBench -> FeedbackLoop -> Productizer ;
- priorisation Bayes-Tristan.
