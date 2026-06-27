# Ω-LEARN-T — Apprentissage de Tristan

Prototype opérationnel pour transformer une compétence en boucle d'apprentissage vérifiable : diagnostic Bayes-Tristan, extraction d'invariants CVCD, mémoire positive/négative, curriculum actif, tests OAK et score de néguentropie cognitive.

## Idée centrale

Apprendre = compresser l'expérience en invariants fertiles, corriger les erreurs comme syndromes, puis décompresser la connaissance en action, prédiction, transfert, explication et création.

```text
Experience -> LOG/CVCD -> MemoryCodec -> Practice -> Feedback -> M-/M+ -> OAKBench -> Canon
```

## Installation locale

```bash
python -m pip install -e .
```

Le prototype utilise uniquement la bibliothèque standard Python.

## Démo rapide

```bash
python -m omega_learn_t.cli diagnose examples/physics_learning.json
python -m omega_learn_t.cli coach examples/physics_learning.json
python -m omega_learn_t.cli oak examples/physics_learning.json
```

## Modules

- `core.py` : dataclasses, axes de maîtrise, état d'apprentissage.
- `cvcd.py` : extraction légère d'invariants, résidus et tokens générateurs.
- `bayes_mastery.py` : suivi Beta/Bayes par axe de compétence.
- `memory_codec.py` : cartes mémoire robustes avec rappel espacé.
- `m_minus_registry.py` : registre M⁻ des erreurs, causes, corrections et tests futurs.
- `curriculum_cvcd.py` : génération de micro-curriculum à partir des axes faibles.
- `oakbench_learn.py` : validation OAK, métriques, score global.
- `sage_learning_coach.py` : orchestrateur zéro-touch pour diagnostic -> plan -> tests.
- `cli.py` : interface terminal.

## Statut OAK

Ce prototype est un MVP de recherche. Il ne prétend pas mesurer parfaitement l'apprentissage humain. Il fournit une architecture falsifiable : chaque score doit être rattaché à des preuves, à des tests actifs et à des résidus.

## Structure de compétence attendue

```json
{
  "skill": "oscillateurs harmoniques",
  "goal": "résoudre et expliquer les problèmes standards et variantes",
  "notes": "force de rappel, énergie, phase, résonance, amortissement",
  "evidence": [
    {"axis": "understanding", "successes": 3, "failures": 1},
    {"axis": "transfer", "successes": 1, "failures": 2}
  ],
  "errors": [
    {
      "name": "confusion fréquence angulaire/fréquence",
      "cause": "unités mélangées",
      "correction": "vérifier omega=2*pi*f",
      "future_test": "convertir f en omega dans 5 problèmes"
    }
  ]
}
```

## Commandes utiles

```bash
python -m omega_learn_t.cli inspect examples/math_learning.json
python -m omega_learn_t.cli cards examples/coding_learning.json
python -m omega_learn_t.cli mminus examples/physics_learning.json
```

## Roadmap

1. Connecter à GitHub Issues/Projects pour transformer les erreurs en tickets OAK.
2. Ajouter sauvegarde SQLite locale.
3. Ajouter import/export Anki.
4. Ajouter scheduler quotidien de rappel.
5. Ajouter benchmarks sur physique, maths, code et AIT-ChessMaster.
