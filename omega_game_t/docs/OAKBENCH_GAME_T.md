# OAKBench-GAME-T

`OAKBench-GAME-T` est le benchmark commun de Ω-GAME-T++.

Il transforme chaque moteur en objet mesurable : `TextWorld-T`, `BoardGame-T`, `ScienceSandbox-T`, `CircuitDungeon-T`, `EnergyCivilization-T`, puis futurs `ProofDetective-T`, `FounderRPG-T`, `PhysicsSandbox-T` et `MyceliumRPG-T`.

## Objectif

```text
world -> replay -> metrics -> quality score -> M+/M- -> next improvement
```

OAKBench ne prouve pas qu'un jeu est parfait. Il donne une mesure reproductible et falsifiable de la qualité minimale d'un monde jouable.

## Métriques

| Champ | Sens |
|---|---|
| `fun` | envie de continuer |
| `agency` | vrais choix |
| `coherence` | monde logique |
| `learning` | apprentissage réel |
| `safety` | absence de manipulation |
| `novelty` | non-répétition |
| `fairness` | difficulté juste |
| `replayability` | divergence entre parties |
| `friction` | confusion ou lourdeur |
| `exploits` | failles de règles ou abus |
| `confusion` | manque de lisibilité |
| `residue` | erreur ou résidu mesuré |
| `compression_gain` | utilité LOG/CVCD |
| `m_minus_reduction` | réduction des erreurs connues |

## Score

```text
Q =
  0.15 * fun
+ 0.15 * agency
+ 0.15 * coherence
+ 0.15 * learning
+ 0.10 * novelty
+ 0.10 * replayability
+ 0.10 * safety
+ 0.05 * fairness
+ 0.05 * compression_gain
+ 0.05 * m_minus_reduction
- 0.05 * exploits
- 0.05 * friction
- 0.05 * confusion
- 0.05 * residue
```

Le score est borné entre `0` et `1`.

## Seuils

| Score | Niveau |
|---|---|
| `Q >= 0.80` | bon moteur |
| `Q >= 0.90` | moteur excellent |
| `Q >= 0.95` | moteur plus ultra |

## Résultat JSON attendu

```json
{
  "engine": "CircuitDungeon-T",
  "quality": 0.89,
  "level": "excellent",
  "metrics": {
    "fun": 0.82,
    "agency": 0.91,
    "coherence": 0.96,
    "learning": 0.88,
    "safety": 1.0,
    "novelty": 0.74,
    "friction": 0.12,
    "exploits": 0.02
  }
}
```

## Règle OAKBench

> Ce qui n'est pas mesuré ne peut pas être amélioré par M+/M-.

OAKBench-GAME-T rend Ω-GAME-T++ mesurable, comparable et améliorable.
