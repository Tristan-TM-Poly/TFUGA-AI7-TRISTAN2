# LaunchForge-T — Ω-GAME-T++

`LaunchForge-T` transforme un `DemoPlan` et un `ProductPlan` en brouillon de lancement interne OAK-safe.

Il prolonge la chaîne :

```text
Theory -> Compiler -> Productizer -> IssueForge -> SprintForge -> DemoForge -> LaunchForge -> LaunchDraft
```

## Rôle

LaunchForge prépare les actifs de lancement : pitch, landing page brouillon, audience, canaux, checklist IP/OAK, statut de revue et prochaines étapes. Il ne publie rien, n'envoie rien, ne vend rien et ne lance aucune action externe.

## Entrée

```yaml
product_plan:
  product_name: CircuitDungeon-T Lesson Pack
  audience:
    - teachers
    - students

demo_plan:
  opening_hook: show the playable learning loop
  success_signals:
    - core_loop_is_visible
```

## Sortie

```yaml
launch_draft:
  title: CircuitDungeon-T Lesson Pack Launch Draft
  status: internal_draft
  public_release: blocked_until_review
  landing_page:
    headline: Learn RLC resonance through playable puzzles
  pitch:
    one_liner: A playable lesson pack for circuit resonance.
  oak_checklist:
    - review IP status
    - keep limits visible
```

## Sections canoniques

1. Landing page draft.
2. Pitch one-liner.
3. Audience and channels.
4. Demo assets to show.
5. OAK/IP checklist.
6. Launch blockers.
7. Next review actions.

## Règle canonique

> LaunchForge-T prépare le lancement, mais ne lance pas.

## Extension prévue

- ProductBench-T ;
- RevenueForge-T ;
- landing page export ;
- pitch deck export ;
- pricing hypothesis ;
- private beta checklist ;
- GitHub Issue export for launch tasks.
