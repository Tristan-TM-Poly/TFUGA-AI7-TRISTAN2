# EnergyCivilization-T — Ω-GAME-T

`EnergyCivilization-T` est une couche jeu et stratégie construite au-dessus de `ScienceSandbox-T` et du modèle `MicrogridStep`.

But : transformer un micro-réseau pédagogique en civilisation jouable. Une colonie possède une batterie, reçoit une production solaire, consomme une charge, subit des pertes, sert ou ne sert pas la demande, puis reçoit un score OAK.

## Formule

```text
EnergyTurn = Solar + Load + Battery + Losses + UnservedDemand + OAK + M+/M-
```

Score pédagogique :

```text
EnergyScore = service_ratio - loss_penalty - unmet_penalty - curtailment_penalty
```

## Règle OAK-energy

EnergyCivilization-T garde visibles :

- les unités ;
- les bornes de batterie ;
- les pertes ;
- la demande servie ;
- la demande non servie ;
- la différence entre jeu, modèle pédagogique et système réel.

## MVP inclus

- `EnergyColony` : état d'une colonie énergétique.
- `EnergyTurnInput` : soleil, charge, durée.
- `EnergyTurnResult` : énergie servie, non servie, pertes, score.
- `EnergyCivilizationEngine` : moteur de tour avec OAK, M+ et M-.
- Démo : colonie solaire avec batterie.
- Tests : score, bornes batterie, mémoire, validation.

## Extensions prévues

1. Marché énergie : prix, rareté, arbitrage.
2. Bâtiments : solaire, batteries, charges critiques, industrie.
3. Météo : profils temporels de production et demande.
4. Résilience : pannes simulées, stockage, priorisation.
5. OAKBench : rendement, service ratio, pertes, stabilité.
6. Hybridation avec `BoardGame-T` : carte de colonies et routes énergétiques.

## Règle canonique

> EnergyCivilization-T transforme les systèmes énergétiques en stratégie jouable, tout en restant un modèle éducatif et vérifiable.
