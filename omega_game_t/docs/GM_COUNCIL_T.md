# GM-Council-T — Ω-GAME-T++

`GM-Council-T` transforme le GameMaster unique en conseil d'agents spécialisés.

Au lieu d'une seule proposition, plusieurs GameMasters analysent le monde selon leurs angles : narration, stratégie, apprentissage, science, économie, mycélium, OAK et mémoire. Le conseil fusionne ensuite ces signaux en une proposition pondérée, validée et mémorisée.

## Formule

```text
GM-Council(World) = OAK(weighted_vote(GM_i(World)))
```

## Agents canoniques

| Agent | Rôle |
|---|---|
| GM-Narrator | tension narrative, arcs, mystères, conséquences |
| GM-Strategist | défi, contre-jeu, choix, difficulté |
| GM-Teacher | apprentissage, feedback, progression |
| GM-Scientist | unités, résidu, modèles, domaine de validité |
| GM-Economist | ressources, rareté, pertes, incitations |
| GM-Mycelium | connexions cachées, synergies, suites fertiles |
| GM-OAK | cohérence, sécurité, non-manipulation, testabilité |
| GM-Memory | M+ et M-, erreurs passées, anti-répétition |

## Processus

1. Chaque agent observe le monde.
2. Chaque agent produit une proposition normalisée.
3. Le conseil pondère les propositions.
4. La meilleure action passe dans OAK.
5. Le résultat accepté va dans M+.
6. Le résultat rejeté ou faible va dans M-.

## Structure d'une proposition

```json
{
  "agent": "GM-Teacher",
  "action": "add_feedback_loop",
  "rationale": "The player needs readable feedback before the next challenge.",
  "scores": {
    "fun": 0.70,
    "agency": 0.80,
    "coherence": 0.90,
    "learning": 0.95,
    "safety": 1.00,
    "novelty": 0.65
  }
}
```

## Règle canonique

> Un GameMaster de Tristan ne dirige pas le joueur : il protège la liberté, augmente la lisibilité et rend le monde plus fertile.

## Extension prévue

- votes Bayes-Tristan ;
- pondération adaptative par moteur ;
- mémoire M- anti-répétition ;
- conseil spécialisé par monde ;
- OAKBench du conseil ;
- intégration avec `WorldDNA` et `RuleGenome`.
