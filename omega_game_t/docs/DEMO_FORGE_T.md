# DemoForge-T — Ω-GAME-T++

`DemoForge-T` transforme un `ProductPlan` et un `SprintPlan` en démonstration interne OAK-safe.

Il prolonge la chaîne :

```text
Theory -> Compiler -> Productizer -> IssueForge -> SprintForge -> DemoForge -> DemoPlan
```

## Rôle

DemoForge prépare une démo : script, narration, scénario, checklist OAK, points de preuve et aperçu Markdown. Il ne publie rien automatiquement et ne lance aucune action externe.

## Entrée

```yaml
product_plan:
  product_name: CircuitDungeon-T Lesson Pack
  target_engine: CircuitDungeon-T

sprint_plan:
  tasks:
    - implement interactive demo
    - add OAKBench report
    - document launch readiness
```

## Sortie

```yaml
demo_plan:
  title: CircuitDungeon-T Lesson Pack Demo
  audience: teachers and students
  opening: show the playable learning loop
  scenes:
    - introduce the product
    - show the core challenge
    - show feedback and OAK notes
    - show next roadmap
  oak_checklist:
    - no external publication
    - limits visible
    - tests referenced
```

## Structure d'une démo

1. Hook : pourquoi le monde existe.
2. World loop : ce que le joueur fait.
3. Moment de preuve : sortie mesurable ou OAKBench.
4. M+/M- : ce qui marche et ce qui est évité.
5. Roadmap : prochaines tâches du sprint.
6. OAK : limites, statut de revue, prudence.

## Règle canonique

> DemoForge-T transforme un prototype en histoire démontrable, sans confondre démonstration, validation scientifique et lancement public.

## Extension prévue

- export vidéo-script ;
- storyboard ;
- capture checklist ;
- démo Android ;
- web demo script ;
- ProductBench integration ;
- LaunchForge-T.
