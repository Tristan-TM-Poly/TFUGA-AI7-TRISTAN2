# RevenueForge-T — Ω-GAME-T+++

`RevenueForge-T` transforme un `LaunchDraft` et un `ProductPlan` en hypothèses de revenus OAK-safe.

Il prolonge la chaîne :

```text
Theory -> Compiler -> Productizer -> DemoForge -> LaunchForge -> RevenueForge -> RevenuePlan
```

## Rôle

RevenueForge prépare offres, hypothèses de prix, canaux privés, signaux de revenu et contrôles OAK. Il ne vend rien, n'envoie rien, ne publie rien et ne crée aucun engagement externe.

## Entrée

```yaml
product_plan:
  product_name: CircuitDungeon-T Lesson Pack
  revenue_paths:
    - education_license
    - premium_puzzle_modules

launch_draft:
  status: internal_draft
  public_release: blocked_until_review
```

## Sortie

```yaml
revenue_plan:
  status: internal_revenue_hypothesis
  offers:
    - basic_lesson_pack
    - premium_pack
  pricing_hypotheses:
    - low
    - medium
    - high
  channels:
    private:
      - internal_demo_review
      - private_feedback_session
  success_signals:
    - asks_price
    - requests_classroom_version
```

## Règles OAK

- Un signal n'est pas encore un revenu.
- Un revenu n'est pas encore une entreprise durable.
- Aucun envoi externe automatique.
- Aucune promesse scientifique sans validation.
- Revue humaine avant tout passage public ou sensible.

## Extension prévue

- ProductBench-T ;
- FeedbackLoop-T ;
- private beta checklist ;
- pricing experiments ;
- revenue memory M+/M- ;
- export vers IssueForge-T.
