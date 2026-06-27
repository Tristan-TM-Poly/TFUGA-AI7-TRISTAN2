# Ω-GAME-T — GameEngines & GameMasters de Tristan

**Statut :** branche canonique / MVP prototypable / OAK-safe.

Ω-GAME-T transforme les jeux, simulations et mondes interactifs en laboratoires vivants de création, apprentissage, stratégie, physique, narration, économie, IA et falsification.

```text
GameWorld_{t+1} = EXP(OAK(GM(CVCD(LOG(HGFM(GameWorld_t, Player_t, Rules_t))))))
```

Traduction :

```text
Monde → compression de l'état → invariants fertiles → GameMaster → événements/quêtes/règles → validation OAK → monde suivant
```

## MVP actuel

Ce dossier contient un MVP Python pour transformer la théorie en artefact exécutable :

- `WorldGraph`, `Entity`, `Event`, `RuleKernel`
- `GameMasterAgent`, `QuestCVCD`, `OAKGate`
- `MPlusMemory` / `MMinusMemory`
- `GameQualityScore`
- `TextWorldEngine`
- `BoardGameEngine`
- `ScienceSandboxEngine`
- `CircuitDungeonEngine`
- exemples `Quest-CVCD`, `BoardGame-T`, `ScienceSandbox-T`, `CircuitDungeon-T`
- tests unitaires
- schémas JSON
- CI GitHub Actions `pytest`

## Moteurs inclus

### TextWorld-T

Moteur texte minimal pour générer des quêtes, événements et traces de monde via GameMaster + CVCD + OAK.

### BoardGame-T

Moteur grille/plateau générique pour roguelike, tactique, pathfinding, stratégie et futurs benchmarks AIT-ChessMaster.

### ScienceSandbox-T

Moteur de simulation jouable et OAK-safe pour transformer des théories scientifiques en expériences inspectables. Le MVP inclut :

- `RLCStep` : circuit RLC série simplifié ;
- `MicrogridStep` : bilan microgrid solaire/batterie/charge/pertes.

Ces modèles sont pédagogiques et prototypables. Ils ne remplacent pas des solveurs physiques validés ni des mesures réelles.

### CircuitDungeon-T

Jeu-puzzle virtuel au-dessus de `ScienceSandbox-T`. Les défis utilisent des circuits RLC et la fréquence de résonance pédagogique :

```text
f0 = 1 / (2π√(LC))
```

Le moteur enregistre les réussites dans M+, les erreurs dans M-, et garde OAK entre simulation pédagogique et réalité physique.

## Structure

```text
omega_game_t/
  README.md
  pyproject.toml
  docs/
    CIRCUIT_DUNGEON_T.md
    OMEGA_GAME_T_MANIFESTO.md
    OAK_GAME_PROTOCOL.md
    SCIENCE_SANDBOX_T.md
  schemas/
    circuit_door.schema.json
    event.schema.json
    oak_report.schema.json
    quest_blueprint.schema.json
    world_graph.schema.json
  omega_game/
    core.py
    cvcd.py
    gm.py
    oak.py
    memory.py
    engines/
      boardgame.py
      circuit_dungeon.py
      science_sandbox.py
      textworld.py
    examples/
      boardgame_t_demo.py
      circuit_dungeon_t_demo.py
      quest_cvcd_demo.py
      science_sandbox_t_demo.py
  tests/
    test_boardgame_t.py
    test_circuit_dungeon_t.py
    test_omega_game_t.py
    test_science_sandbox_t.py
```

## Règle OAK

> Un jeu de Tristan doit maximiser l'émergence, pas l'addiction.

Ω-GAME-T peut entraîner, inspirer, simuler et enseigner, mais il ne doit pas manipuler, radicaliser, exploiter ou tromper.
