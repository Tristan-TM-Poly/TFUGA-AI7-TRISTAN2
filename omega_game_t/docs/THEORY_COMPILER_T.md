# TheoryCompiler-T — Ω-GAME-T++

`TheoryCompiler-T` est le compilateur de théories vers mondes jouables.

Il transforme une branche du corpus de Tristan en artefacts vérifiables :

```text
TheorySpec -> WorldDNA + RuleGenome + target_engine + product_path + OAK notes
```

## Rôle

Le Reality Compiler devient concret : une théorie n'est pas seulement décrite, elle est compilée en monde jouable, benchmarkable et améliorable.

## Entrée

```yaml
theory:
  name: Ω-CIRCUITS-T
  concepts:
    - RLC
    - resonance
    - impedance
    - phase
  constraints:
    - virtual_model
    - visible_units
    - OAK_safe
```

## Sortie

```yaml
compiled_world:
  theory: Ω-CIRCUITS-T
  target_engine: CircuitDungeon-T
  world_dna:
    name: CircuitDungeon-T
    genre: educational_puzzle
  rule_genomes:
    - rlc_resonance_gate
  product_path:
    - demo
    - lesson_pack
    - web_prototype
    - paid_module
```

## Mappings canoniques MVP

| Théorie | Engine cible |
|---|---|
| Ω-CIRCUITS-T | CircuitDungeon-T |
| Ω-ENERGY-T | EnergyCivilization-T |
| Ω-PREUVE-T | ProofDetective-T |
| Ω-COMP-REV-IP | FounderRPG-T |
| Ω-MECH / Ω-PFT / Ω-LASER / Ω-BAT | PhysicsSandbox-T |
| Ω-GAME-T | MyceliumRPG-T |

## Règle OAK

Le compilateur ne prouve pas la théorie. Il crée une **incarnation jouable** avec limites, invariants, mémoire et tests.

## Utilité

- transformer le corpus en mondes ;
- générer des prototypes ;
- créer des jeux sérieux ;
- produire des benchmarks IA ;
- préparer IP, pitch, démos et produits ;
- relier théorie, code, tests, mémoire et revenus.

## Prochaine extension

- compiler automatiquement vers fichiers de jeu ;
- créer des niveaux depuis `RuleGenome` ;
- intégrer `OAKBench-GAME-T` ;
- générer issues GitHub par monde ;
- générer pitch decks et pages produit.
