# Ω-GAME-T — GameEngines & GameMasters de Tristan

**Statut :** branche canonique / MVP prototypable / OAK-safe.

Ω-GAME-T transforme les jeux, simulations et mondes interactifs en laboratoires vivants de création, apprentissage, stratégie, physique, narration, économie, IA et falsification.

```text
GameWorld_{t+1} = EXP(OAK(GM(CVCD(LOG(HGFM(GameWorld_t, Player_t, Rules_t))))))
```

Traduction :

```text
Monde → compression de l’état → invariants fertiles → GameMaster → événements/quêtes/règles → validation OAK → monde suivant
```

## Deux piliers

### Ω-GAMEENGINE-T — GameEngines de Tristan

Un GameEngine de Tristan n’est pas seulement un moteur de rendu, de physique ou d’input. C’est un **moteur de réalité jouable** :

```text
GameEngine_T = Renderer + Physics + Rules + Agents + Narrative + Economy + Memory + OAK
```

Il sert à créer des jeux vidéo, simulations scientifiques, mondes de test pour IA, laboratoires de stratégie, jeux éducatifs, mondes RPG, écosystèmes multi-agents et prototypes interactifs des théories de Tristan.

### Ω-GAMEMASTER-T — GameMasters de Tristan

Un GameMaster de Tristan est un agent-orchestrateur :

```text
GameMaster_T = Observer + Narrator + Balancer + Judge + WorldWeaver + OAKGate
```

Principe central :

> Le GameMaster ne contrôle pas le joueur. Il amplifie la liberté jouable tout en maintenant cohérence, tension, justice et émergence.

## Noyau HGFM du jeu

Dans Ω-GAME-T, un jeu est un hypergraphe fractal mycélien dynamique :

```text
G_t = (V_t, E_t, H_t, R_t, M_t)
```

- `V_t` : entités — joueur, PNJ, objets, lieux, ressources, sorts, armes, idées.
- `E_t` : relations — attaque, échange, dialogue, causalité, possession, alliance.
- `H_t` : hyperarêtes — quêtes, factions, économies, conflits, systèmes physiques.
- `R_t` : règles.
- `M_t` : mémoire du monde.

## MVP actuel

Ce dossier contient un MVP minimal Python pour transformer la théorie en artefact exécutable :

- `WorldGraph`
- `Entity`
- `Event`
- `RuleKernel`
- `GameMasterAgent`
- `QuestCVCD`
- `OAKGate`
- `MPlusMemory` / `MMinusMemory`
- `GameQualityScore`
- `TextWorldEngine`
- `BoardGameEngine`
- `ScienceSandboxEngine`
- exemples `Quest-CVCD`, `BoardGame-T`, `ScienceSandbox-T`
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

## Structure

```text
omega_game_t/
  README.md
  pyproject.toml
  docs/
    OMEGA_GAME_T_MANIFESTO.md
    OAK_GAME_PROTOCOL.md
    SCIENCE_SANDBOX_T.md
  schemas/
    event.schema.json
    oak_report.schema.json
    quest_blueprint.schema.json
    world_graph.schema.json
  omega_game/
    __init__.py
    core.py
    cvcd.py
    gm.py
    oak.py
    memory.py
    engines/
      __init__.py
      boardgame.py
      science_sandbox.py
      textworld.py
    examples/
      __init__.py
      boardgame_t_demo.py
      quest_cvcd_demo.py
      science_sandbox_t_demo.py
  tests/
    test_boardgame_t.py
    test_omega_game_t.py
    test_science_sandbox_t.py
```

## Règle OAK

> Un jeu de Tristan doit maximiser l’émergence, pas l’addiction.

Ω-GAME-T peut entraîner, inspirer, simuler et enseigner, mais il ne doit pas manipuler, radicaliser, exploiter ou tromper.
