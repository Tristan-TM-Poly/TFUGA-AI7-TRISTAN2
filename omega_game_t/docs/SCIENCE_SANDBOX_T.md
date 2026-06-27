# ScienceSandbox-T — Ω-GAME-T

`ScienceSandbox-T` transforme les théories scientifiques de Tristan en expériences jouables, prudentes et falsifiables.

Objectif : créer un pont entre :

```text
théorie → simulation minimale → événement jouable → OAK → mesure → mémoire M+/M-
```

## Règle OAK-science

Une simulation ScienceSandbox-T doit toujours distinguer :

- modèle pédagogique ;
- approximation numérique ;
- hypothèse fertile ;
- résultat validé ;
- preuve expérimentale.

Elle ne doit jamais présenter une expérience virtuelle comme une validation physique réelle.

## MVP inclus

Ce passage ajoute deux mini-modèles dépendance-zéro :

1. `RLCStep` — circuit RLC série simplifié par intégration d'Euler semi-explicite.
2. `MicrogridStep` — bilan microgrid simplifié : solaire, batterie, charge, pertes, unmet demand.

Ces modèles sont volontairement simples, lisibles, testables et OAK-safe.

## Invariants suivis

### RLC

- énergie condensateur ;
- énergie inductance ;
- perte Joule ;
- courant ;
- charge ;
- tension source.

### Microgrid

- énergie batterie ;
- demande servie ;
- demande non servie ;
- énergie perdue ;
- énergie solaire utilisée ;
- énergie solaire écrêtée.

## Extension prévue

- `CircuitDungeon` : portes, filtres, impédance, résonance, phase.
- `EnergyCivilization` : microgrids, batteries, stabilité, coûts, rendement.
- `PhysicsSandbox` : fluides, optique, lasers, MEMS, gravité, CPUFMT.
- `OAKBench-Science` : conservation, unités, stabilité numérique, résidus.

## Clause de prudence

ScienceSandbox-T est un outil de simulation et d'apprentissage. Il ne remplace pas des solveurs physiques validés, des mesures réelles, un encadrement professionnel ou des normes de sécurité électrique/laser/plasma/batterie.
