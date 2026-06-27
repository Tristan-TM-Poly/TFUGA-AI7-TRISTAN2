# CircuitDungeon-T — Ω-GAME-T

`CircuitDungeon-T` est le premier jeu-puzzle construit au-dessus de `ScienceSandbox-T`.

Idée : transformer les circuits RLC en portes, verrous, salles, fréquences, résonances, filtres et choix tactiques. Le joueur ne résout pas seulement un calcul : il apprend à lire une dynamique physique comme une règle de monde.

## Formule

```text
CircuitDoor = RLCParams + resonance_target + tolerance + OAK + M+/M-
```

Une porte peut être ouverte si la fréquence proposée par le joueur tombe dans la fenêtre de résonance autorisée :

```text
f0 = 1 / (2π√(LC))
```

## Règle OAK-science

CircuitDungeon-T doit rester pédagogique et sûr :

- basse tension virtuelle seulement ;
- aucune instruction de montage réel dangereux ;
- aucune promesse de validation physique réelle ;
- unités visibles ;
- erreurs et approximations enregistrées dans M⁻ ;
- succès enregistrés dans M⁺ ;
- chaque puzzle doit avoir un signal mesurable.

## MVP inclus

- `CircuitDoor` : porte RLC avec paramètres et tolérance.
- `CircuitDungeonEngine` : ajoute joueur, portes, essais de fréquence, OAK et mémoire.
- Démo : ouverture d’une porte proche de sa résonance, rejet d’un mauvais essai.
- Tests : fréquence de résonance, ouverture/réjection, mémoire M⁺/M⁻, validation des paramètres.

## Extension prévue

1. `FilterRoom` : filtres passe-bas, passe-haut, passe-bande.
2. `ImpedanceBridge` : choix de chemins selon impédance complexe.
3. `PhaseLockGate` : puzzles de phase.
4. `EnergyBudgetDungeon` : énergie limitée, pertes Joule, stratégie.
5. `CircuitDungeon + BoardGame-T` : plateau où chaque porte est un circuit.
6. `AIT-ChessMaster` : raisonnement tactique sur circuits comme coups et contre-coups.

## Règle canonique

> CircuitDungeon-T transforme l’électronique en monde jouable, mais garde OAK entre simulation, pédagogie et réalité physique.
