# Architecture interne R0.2

## Pipeline

```text
AlgorithmSpec
  → KernelIR
  → VariantAddress
  → Static OAK Gate
  → Source Generator
  → Compiler Adapter
  → Differential Tests
  → Benchmark Protocol
  → Pareto Selector
  → M⁺/M⁻ Ledger
```

## Invariants

1. Une adresse logique est indépendante de l’ordre d’exécution d’une campagne.
2. Le même contenu produit le même identifiant.
3. `address_at(index)` et `index_of(address)` sont inverses.
4. Une variante incorrecte est exclue de toute sélection.
5. Les sorties massives sont shardées et hashées.
6. Le manifest est écrit après chaque shard.
7. Une reprise doit reproduire le même manifest final.
8. Les claims scientifiques et les gagnants universels restent explicitement faux.

## Frontière mixte-radix

La frontière n’est jamais construite sous forme d’une liste de milliards d’objets. L’index global est décomposé selon les cardinalités de chaque axe. Le coût mémoire de l’accès à une cellule reste constant par rapport à la taille totale de la frontière.

## Génération certifiée et recherche

Le catalogue représente des spécifications de recherche. En R0.2, le générateur exécutable complet est volontairement limité au kernel affine, parce qu’un générateur générique non validé pourrait créer rapidement beaucoup de code incorrect. Les autres cellules restent `LOGICAL` jusqu’à l’ajout d’un lowering, de tests différentiels et d’un protocole de compilation propres à leur famille.

## Extension prévue

- lowering pour réductions avec politique d’ordre explicite;
- kernels matriciels et tenseurs;
- FFWT/FWT/FFT;
- graphes CSR et hypergraphes;
- compilateurs CMake/Cargo autonomes;
- sanitizers C/C++ et Miri Rust;
- séparation kernel-only, conversion-only et end-to-end;
- historique par empreinte matérielle;
- campagnes pilotées par valeur d’information;
- artefacts GitHub compressés plutôt que binaires committés.
