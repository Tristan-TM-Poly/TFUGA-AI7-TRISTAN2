# Productizer-T — Ω-GAME-T++

`Productizer-T` transforme un `CompiledWorld` en plan produit OAK-safe.

Il prolonge la chaîne :

```text
Theory -> TheoryCompiler -> CompiledWorld -> Productizer -> ProductPlan -> launch roadmap
```

## Rôle

Le Productizer ne publie rien automatiquement et ne fait aucune action externe. Il prépare un plan structuré : public cible, proposition de valeur, livrables, modèle de revenu, risques, contrôles OAK et prochaines étapes.

## Entrée

```yaml
compiled_world:
  theory: Ω-CIRCUITS-T
  target_engine: CircuitDungeon-T
  world_dna: ...
  rule_genomes: ...
  product_path:
    - demo
    - lesson_pack
    - web_prototype
    - paid_module
```

## Sortie

```yaml
product_plan:
  product_name: CircuitDungeon-T Lesson Pack
  audience:
    - students
    - teachers
  value_props:
    - learn RLC resonance through playable puzzles
  deliverables:
    - demo
    - lesson pack
    - OAKBench report
  revenue_paths:
    - school license
    - premium modules
  ip_classification: review_before_public_release
  oak_controls:
    - review IP status before public release
    - keep simulations educational
```

## Plans canoniques MVP

| Engine | Produit |
|---|---|
| CircuitDungeon-T | pack éducatif circuits / jeu puzzle |
| EnergyCivilization-T | serious game énergie / microgrid strategy |
| ProofDetective-T | formation enquête probatoire |
| FounderRPG-T | outil incubateur / startup RPG |
| PhysicsSandbox-T | laboratoire interactif de modèles |
| MyceliumRPG-T | univers de recherche jouable |
| TextWorld-T | démo narrative générique |

## Règles OAK-IP-revenus

- Classer l'actif avant une publication publique.
- Séparer : public, interne, à revoir, protégé, marque/design.
- Ne pas prétendre validation scientifique si le monde est seulement pédagogique.
- Garder une validation humaine pour décisions légales, IP, vente externe ou publication sensible.

## Utilité

- transformer les mondes en produits ;
- générer pitch, roadmap et modules ;
- préparer revenus actifs/passifs ;
- relier science, pédagogie, IP et GitHub ;
- produire une file de prochaines actions concrètes.

## Extension prévue

- générateur de pitch deck ;
- générateur de landing page ;
- générateur de licence ;
- matrice IP ;
- roadmap de revenus ;
- export vers GitHub Issues ;
- OAK ProductBench.
