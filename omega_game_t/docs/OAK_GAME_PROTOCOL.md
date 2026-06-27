# OAK Game Protocol — Ω-GAME-T

OAK est le gardien de Ω-GAME-T. Il valide qu’une règle, quête, rencontre, récompense, simulation ou intervention du GameMaster reste cohérente, juste, sûre, testable et non exploitative.

```text
OAK(GameEvent) = Fair? + Fun? + Coherent? + Safe? + Testable? + NonExploitative?
```

## Critères minimaux

| Critère | Question | Échec typique |
|---|---|---|
| Cohérence | Compatible avec le monde et les règles ? | PNJ incohérent, causalité brisée |
| Équité | Le joueur a-t-il une chance lisible ? | Difficulté arbitraire, punition invisible |
| Intérêt | Est-ce ludique, tendu ou apprenant ? | Quête plate, répétition, grind vide |
| Non-manipulation | Évite-t-on les dark patterns ? | Addiction, pression artificielle, récompense prédatrice |
| Sécurité | Évite-t-on contenu dangereux ou abusif ? | Incitation nuisible, simulation mal cadrée |
| Mesure | Peut-on observer si ça marche ? | Aucun signal, aucune métrique |
| Mémoire négative | Que faut-il éviter la prochaine fois ? | Bug oublié, exploit récurrent |

## Règles strictes

Ω-GAME-T doit éviter :

- dark patterns ;
- loot boxes prédatrices ;
- manipulation addictive ;
- collecte abusive de données ;
- génération de contenu toxique ;
- triche ou bots pour jeux en ligne ;
- simulations dangereuses présentées comme réalité ;
- confusion entre entraînement virtuel et compétence réelle ;
- usage militaire/violence opérationnelle ;
- remplacement non supervisé d’un enseignant, clinicien ou expert.

## GameQualityScore

Chaque moteur ou GameMaster doit être mesuré par un score composite :

```text
GameQuality =
  w1 * Fun
+ w2 * Agency
+ w3 * Coherence
+ w4 * Novelty
+ w5 * Fairness
+ w6 * Learning
- w7 * Friction
- w8 * Exploits
```

Métriques canoniques :

| Métrique | Question |
|---|---|
| FunScore | Le joueur veut-il continuer ? |
| AgencyScore | Le joueur a-t-il de vrais choix ? |
| CoherenceScore | Le monde reste-t-il logique ? |
| NoveltyScore | Le contenu est-il non répétitif ? |
| FairnessScore | La difficulté est-elle juste ? |
| LearningScore | Le joueur apprend-il quelque chose ? |
| ReplayValue | Les parties divergent-elles vraiment ? |
| ExploitResistance | Peut-on casser le système ? |
| SafetyScore | Évite-t-il manipulation/danger ? |
| CompressionGain | LOG/CVCD réduit-il bien l’état ? |

## Seuils MVP

Pour le MVP, un événement est accepté si :

```text
coherent == true
fair == true
safe == true
non_exploitative == true
agency >= 0.5
```

Tout événement rejeté doit créer une entrée M⁻ avec la raison du rejet.

## Règle OAK finale

> Le jeu peut entraîner, inspirer, simuler et enseigner, mais il ne doit pas manipuler, radicaliser, exploiter ou tromper.
