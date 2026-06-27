# IssueForge-T — Ω-GAME-T++

`IssueForge-T` transforme un `ProductPlan` en roadmap GitHub-ready.

Il prolonge la chaîne :

```text
Theory -> TheoryCompiler -> Productizer -> ProductPlan -> IssueForge -> IssueSet -> Sprint-ready roadmap
```

## Rôle

IssueForge prépare des issues structurées. Il ne crée pas automatiquement de vraies issues GitHub et ne publie rien hors du dépôt. La sortie est un objet sérialisable que l'on peut relire, valider, commenter, tester, puis éventuellement transformer en issues réelles avec approbation humaine.

## Entrée

```yaml
product_plan:
  product_name: CircuitDungeon-T Lesson Pack
  target_engine: CircuitDungeon-T
  deliverables:
    - interactive_demo
    - lesson_pack
    - oakbench_report
  oak_controls:
    - review_ip_status_before_public_release
    - run_oakbench_before_launch
```

## Sortie

```yaml
issue_set:
  epic_title: Build CircuitDungeon-T Lesson Pack
  milestone: CircuitDungeon-T MVP
  labels:
    - omega-game-t
    - product
    - oak-safe
  issues:
    - title: Add interactive demo for CircuitDungeon-T Lesson Pack
    - title: Add lesson pack for CircuitDungeon-T Lesson Pack
    - title: Add OAKBench report for CircuitDungeon-T Lesson Pack
```

## Types d'issues MVP

1. Livrable produit.
2. Contrôle OAK.
3. Test/validation.
4. Documentation.
5. Démo.
6. Risque à réduire.

## Critères d'acceptation canoniques

Chaque issue doit contenir :

- produit source ;
- théorie source ;
- moteur cible ;
- valeur attendue ;
- critères d'acceptation ;
- contrôles OAK ;
- mémoire positive attendue ;
- mémoire négative évitée.

## Règle OAK

> IssueForge-T organise le travail. Il ne remplace pas la revue humaine avant publication, vente, revendication scientifique ou action externe.

## Extension prévue

- export Markdown par issue ;
- création réelle d'issues GitHub après approbation ;
- groupement en milestones ;
- priorisation P0/P1/P2 ;
- SprintForge-T ;
- ProductBench-T ;
- LaunchForge-T.
