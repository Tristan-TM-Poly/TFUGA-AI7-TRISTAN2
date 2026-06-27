# Ω-GAME-T — GameEngines & GameMasters de Tristan

**Statut :** branche canonique / MVP prototypable / OAK-safe / Ω-GAME-T++ en cours.

Ω-GAME-T transforme les jeux, simulations et mondes interactifs en laboratoires vivants de création, apprentissage, stratégie, physique, narration, économie, IA et falsification.

```text
GameWorld_{t+1} = EXP(OAK(GM(CVCD(LOG(HGFM(GameWorld_t, Player_t, Rules_t))))))
```

Ω-GAME-T++ ajoute le concept de **Reality Compiler** : transformer une théorie en monde jouable, mesurable et améliorable.

```text
Theory -> TheoryCompiler -> RuleGenome -> WorldDNA -> Engine -> GM-Council -> OAKBench -> Productizer -> IssueForge -> SprintForge -> M+/M- -> Better World
```

## MVP actuel

Ce dossier contient un MVP Python pour transformer la théorie en artefact exécutable :

- `WorldGraph`, `Entity`, `Event`, `RuleKernel`
- `GameMasterAgent`, `QuestCVCD`, `OAKGate`
- `GMCouncil`, `GMVote`, `CouncilScores`
- `TheoryCompiler`, `TheorySpec`, `CompiledWorld`, `WorldDNA`, `RuleGenome`
- `Productizer`, `ProductPlan`
- `IssueForge`, `IssueSet`, `IssueSpec`
- `SprintForge`, `SprintPlan`, `SprintTask`
- `MPlusMemory` / `MMinusMemory`
- `GameQualityScore`
- `TextWorldEngine`
- `BoardGameEngine`
- `ScienceSandboxEngine`
- `CircuitDungeonEngine`
- `EnergyCivilizationEngine`
- `OAKBenchRunner`
- exemples `Quest-CVCD`, `BoardGame-T`, `ScienceSandbox-T`, `CircuitDungeon-T`, `EnergyCivilization-T`, `OAKBench-GAME-T`, `GM-Council-T`, `TheoryCompiler-T`, `Productizer-T`, `IssueForge-T`, `SprintForge-T`
- tests unitaires
- schémas JSON
- CI GitHub Actions `pytest`

## Moteurs inclus

### TextWorld-T

Moteur texte minimal pour générer des quêtes, événements et traces de monde via GameMaster + CVCD + OAK.

### BoardGame-T

Moteur grille/plateau générique pour roguelike, tactique, pathfinding, stratégie et futurs benchmarks AIT-ChessMaster.

### ScienceSandbox-T

Moteur de simulation jouable et OAK-safe. Le MVP inclut :

- `RLCStep` : circuit RLC série simplifié ;
- `MicrogridStep` : bilan microgrid solaire/batterie/charge/pertes.

### CircuitDungeon-T

Jeu-puzzle virtuel au-dessus de `ScienceSandbox-T`. Les défis utilisent des circuits RLC et une fréquence de résonance pédagogique.

### EnergyCivilization-T

Jeu-stratégie virtuel au-dessus de `MicrogridStep`. Une colonie possède une batterie, reçoit une production solaire, consomme une charge, subit des pertes, sert ou ne sert pas la demande, puis reçoit un score énergétique OAK.

### GM-Council-T

Conseil de GameMasters spécialisés : Narrator, Strategist, Teacher, Scientist, Economist, Mycelium, OAK et Memory. Chaque agent vote, le conseil choisit l'action pondérée, OAK valide, puis M+/M- apprend.

### OAKBench-GAME-T

Benchmark commun pour mesurer les moteurs avec : fun, agency, coherence, learning, safety, novelty, fairness, replayability, friction, exploits, confusion, residue, compression gain et M-minus reduction.

### TheoryCompiler-T

Compilateur de théories vers mondes jouables. Il transforme une branche Tristan en `CompiledWorld` : engine cible, `WorldDNA`, `RuleGenome`, notes OAK et chemin produit.

### Productizer-T

Planificateur produit OAK-safe. Il transforme un `CompiledWorld` en `ProductPlan` : public cible, valeur, livrables, chemins de revenus, classification IP à revoir, contrôles OAK et étapes de lancement.

### IssueForge-T

Générateur de roadmaps GitHub-ready. Il transforme un `ProductPlan` en `IssueSet` : epic, milestone, labels, issues, critères d'acceptation, contrôles OAK et export Markdown. Il ne crée pas automatiquement de vraies issues.

### SprintForge-T

Générateur de sprint OAK-safe. Il transforme un `IssueSet` en `SprintPlan` : tâches priorisées, estimations, ordre d'exécution, OAK gates, Definition of Done et export Markdown. Il ne modifie pas de calendrier ni de projet externe.

## Structure

```text
omega_game_t/
  docs/
    CIRCUIT_DUNGEON_T.md
    ENERGY_CIVILIZATION_T.md
    GM_COUNCIL_T.md
    ISSUE_FORGE_T.md
    OAKBENCH_GAME_T.md
    OMEGA_GAME_T_MANIFESTO.md
    OMEGA_GAME_T_PLUS_PLUS.md
    OAK_GAME_PROTOCOL.md
    PRODUCTIZER_T.md
    SCIENCE_SANDBOX_T.md
    SPRINT_FORGE_T.md
    THEORY_COMPILER_T.md
  schemas/
    circuit_door.schema.json
    compiled_world.schema.json
    energy_colony.schema.json
    event.schema.json
    gm_vote.schema.json
    issue_set.schema.json
    oak_report.schema.json
    oakbench_result.schema.json
    product_plan.schema.json
    quest_blueprint.schema.json
    rule_genome.schema.json
    sprint_plan.schema.json
    world_dna.schema.json
    world_graph.schema.json
  omega_game/
    bench/
      oakbench_game.py
    engines/
      boardgame.py
      circuit_dungeon.py
      energy_civilization.py
      science_sandbox.py
      textworld.py
    examples/
      boardgame_t_demo.py
      circuit_dungeon_t_demo.py
      energy_civilization_t_demo.py
      gm_council_t_demo.py
      issue_forge_t_demo.py
      oakbench_game_t_demo.py
      productizer_t_demo.py
      quest_cvcd_demo.py
      science_sandbox_t_demo.py
      sprint_forge_t_demo.py
      theory_compiler_t_demo.py
    forge/
      issue_forge.py
      sprint_forge.py
    gm_council.py
    productizer.py
    theory_compiler.py
  tests/
    test_boardgame_t.py
    test_circuit_dungeon_t.py
    test_energy_civilization_t.py
    test_gm_council_t.py
    test_issue_forge_t.py
    test_oakbench_game_t.py
    test_omega_game_t.py
    test_productizer_t.py
    test_science_sandbox_t.py
    test_sprint_forge_t.py
    test_theory_compiler_t.py
```

## Règle OAK

> Un jeu de Tristan doit maximiser l'émergence, pas l'addiction.

Ω-GAME-T peut entraîner, inspirer, simuler et enseigner, mais il ne doit pas manipuler, radicaliser, exploiter ou tromper.
