# GameEngineOS-T — Ω-GAME-T+++

`GameEngineOS-T` est le noyau commun pour transformer les créations de Tristan en mondes simulables, jouables, mesurables et OAK-safe.

Il étend la chaîne :

```text
Creation -> WorldState -> GameEngineKernel -> SimulationResult -> OAK/M+/M- -> Better Creation
```

## Rôle

GameEngineOS-T n'est pas un jeu unique. C'est un système d'exploitation minimal pour moteurs de simulation : prototypes, énergie, procédés abstraits, recyclage, revenus, code, GitHub, langues humaines et GameMasters.

## Noyau commun

Chaque moteur partage :

- `WorldState` : état du monde ;
- `ResourceFlow` : flux énergie/matière/valeur/connaissance ;
- `Action` : action simulée ;
- `SimulationResult` : sortie mesurée ;
- `ScoreReport` : score borné ;
- `GameEngineKernel` : observe, propose, simule, score, OAK, mémoire.

## Flux fondamentaux

```text
E = energy
M = matter
V = value
K = knowledge
```

Tout prototype consomme, produit ou transforme au moins un de ces flux.

## Moteurs MVP

### PrototypeWorldEngine

Simule les prototypes comme des mondes de décision : tests, docs, demo, OAK, revenus, M+/M-.

### ProcessAlchemyEngine

Simule des procédés abstraits et sûrs : transformation générique, séparation, purification conceptuelle, recyclage, contrôle qualité. Aucun protocole réel ni instruction de manipulation.

### CodeDojoEngine

Transforme le code et les langages de programmation en quêtes : lire, tester, refactorer, documenter, sécuriser, benchmarker.

## Règles OAK

- Simulation seulement pour énergie, procédés, fabrication et recyclage.
- Pas de protocole dangereux.
- Pas de haute tension, chimie pratique, laser réel ou fabrication réelle sans encadrement qualifié.
- Pas de promesse de revenu, performance industrielle ou validation scientifique.
- Pas d'action GitHub destructive automatique.
- Les GameMasters doivent exposer limites, hypothèses, risques et mémoire négative.

## Extension prévue

- EnergyEngine ;
- ManufacturingDungeon ;
- RecyclingLoop ;
- RevenueEmpire ;
- GitHubRealm ;
- PolyglotLanguageEngine ;
- GameMasterAcademy ;
- EngineBench ;
- GameMasterBench.
