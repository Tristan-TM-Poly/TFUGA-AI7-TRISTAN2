# SprintForge-T — Ω-GAME-T++

`SprintForge-T` transforme un `IssueSet` en sprint priorisé, lisible et OAK-safe.

Il prolonge la chaîne :

```text
Theory -> Compiler -> Productizer -> IssueForge -> IssueSet -> SprintForge -> SprintPlan
```

## Rôle

SprintForge prépare un plan de travail. Il ne modifie pas de calendrier, ne crée pas de tâche externe et ne lance aucune action distante. Il produit un objet sérialisable : tâches, ordre, estimations, critères de fin et contrôles OAK.

## Entrée

```yaml
issue_set:
  epic_title: Build CircuitDungeon-T Lesson Pack
  issues:
    - title: Add interactive demo
      priority: p0
    - title: Add OAKBench report
      priority: p0
    - title: Prepare launch-readiness checklist
      priority: p1
```

## Sortie

```yaml
sprint:
  name: CircuitDungeon-T MVP Sprint
  cadence: 7_days
  tasks:
    - implement interactive demo
    - add OAKBench report
    - document launch readiness
  oak_gates:
    - tests_before_done
    - limits_visible
    - no_external_release
```

## Priorisation

Ordre par défaut :

1. `p0` avant `p1` avant `p2`.
2. Bench/OAK avant launch.
3. Démo et livrable principal avant polish.
4. Risques critiques avant diffusion.

## Definition of Done

Chaque tâche est complète seulement si :

- le livrable est présent ;
- les tests ou notes de validation existent ;
- les limites OAK sont visibles ;
- le README ou la démo référence le changement ;
- M+ et M- attendus sont mentionnés.

## Règle canonique

> SprintForge-T transforme la roadmap en exécution, sans enlever les verrous OAK.

## Extension prévue

- Sprint velocity ;
- dépendances entre tâches ;
- export Markdown ;
- intégration GitHub Projects ;
- SprintBench ;
- priorisation Bayes-Tristan ;
- génération de branches par sprint après approbation.
