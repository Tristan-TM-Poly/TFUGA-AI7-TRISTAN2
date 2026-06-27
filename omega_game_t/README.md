# Ω-GAME-T — GameEngines & GameMasters de Tristan

**Statut :** branche canonique / MVP prototypable / OAK-safe / Ω-GAME-T+++ en cours.

Ω-GAME-T transforme les jeux, simulations et mondes interactifs en laboratoires vivants de création, apprentissage, stratégie, physique, narration, économie, IA et falsification.

```text
GameWorld_{t+1} = EXP(OAK(GM(CVCD(LOG(HGFM(GameWorld_t, Player_t, Rules_t))))))
```

Ω-GAME-T+++ ajoute le concept de **Reality Compiler** : transformer une théorie en monde jouable, mesurable, démontrable, organisable, productisable et améliorable par feedback/version.

```text
Creation -> GameEngineOS -> GameMasterAcademy -> TheoryCompiler -> RuleGenome -> WorldDNA -> Engine -> GM-Council -> OAKBench -> Productizer -> IssueForge -> SprintForge -> DemoForge -> LaunchForge -> RevenueForge -> ProductBench -> FeedbackLoop -> VersionForge -> M+/M- -> Better World
```

## MVP actuel

Ce dossier contient un MVP Python pour transformer la théorie en artefact exécutable :

- `WorldGraph`, `Entity`, `Event`, `RuleKernel`
- `GameMasterAgent`, `QuestCVCD`, `OAKGate`
- `GMCouncil`, `GMVote`, `CouncilScores`
- `GameEngineKernel`, `WorldState`, `ResourceFlow`, `Action`, `SimulationResult`
- `PrototypeWorldEngine`, `ProcessAlchemyEngine`, `CodeDojoEngine`, `GitHubRealmEngine`
- `RepoWorld`, `RepoZone`, `RepoQuest`
- `GameMasterAcademy`, `GameMasterProfile`, `TrainingQuest`, `EvaluationRubric`, `AcademyEvaluation`
- `TheoryCompiler`, `TheorySpec`, `CompiledWorld`, `WorldDNA`, `RuleGenome`
- `Productizer`, `ProductPlan`
- `IssueForge`, `IssueSet`, `IssueSpec`
- `SprintForge`, `SprintPlan`, `SprintTask`
- `DemoForge`, `DemoPlan`, `DemoScene`
- `LaunchForge`, `LaunchDraft`, `LandingPageDraft`, `PitchDraft`
- `RevenueForge`, `RevenuePlan`, `OfferSpec`, `PricingHypothesis`, `ChannelMap`, `RevenueSignal`
- `ProductBench`, `ProductBenchMetrics`, `ProductBenchResult`
- `FeedbackLoop`, `FeedbackLoopResult`, `FeedbackSignal`, `FeedbackDecision`
- `VersionForge`, `VersionPlan`, `VersionChange`, `ReleaseCriteria`
- `MPlusMemory` / `MMinusMemory`
- `GameQualityScore`
- `TextWorldEngine`
- `BoardGameEngine`
- `ScienceSandboxEngine`
- `CircuitDungeonEngine`
- `EnergyCivilizationEngine`
- `OAKBenchRunner`
- exemples `Quest-CVCD`, `BoardGame-T`, `ScienceSandbox-T`, `CircuitDungeon-T`, `EnergyCivilization-T`, `OAKBench-GAME-T`, `GM-Council-T`, `GameEngineOS-T`, `GitHubRealmEngine-T`, `GameMasterAcademy-T`, `TheoryCompiler-T`, `Productizer-T`, `IssueForge-T`, `SprintForge-T`, `DemoForge-T`, `LaunchForge-T`, `RevenueForge-T`, `ProductBench-T`, `FeedbackLoop-T`, `VersionForge-T`
- tests unitaires
- schémas JSON
- CI GitHub Actions `pytest`

## GameEngineOS-T

GameEngineOS-T est le noyau commun pour transformer les créations de Tristan en mondes simulables. Il ajoute :

- `WorldState` pour représenter un monde ;
- `ResourceFlow` pour suivre énergie, matière, valeur et connaissance ;
- `Action` pour représenter un choix simulé ;
- `SimulationResult` pour produire score, OAK status, M+ et M- ;
- `GameEngineKernel` pour orchestrer les moteurs.

### PrototypeWorldEngine

Simule les prototypes comme des mondes de décision : tests, démo, scope, clarté, testabilité, M+/M-.

### ProcessAlchemyEngine

Simule des procédés abstraits et sûrs : transformation conceptuelle, qualité, circularité et recyclage générique. Il ne produit aucun protocole réel.

### CodeDojoEngine

Transforme la programmation en quêtes : lire les invariants, ajouter des tests, faire un petit refactor, écrire la documentation.

### GitHubRealmEngine

Transforme un dépôt en carte jouable de maintenance : zones docs/code/tests/schemas/examples/OAK, quêtes, score de santé repo, M+/M-. Il produit des recommandations simulées seulement.

### GameMasterAcademy-T

Forme des GameMasters spécialisés via profils, quêtes, skill scores, rubriques, M+/M- et prochaines quêtes. Le MVP inclut RepoGM, CodeGM, EnergyGM, ProcessGM, RevenueGM et LanguageGM. L'évaluation est interne et ne prétend pas produire une certification officielle externe.

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

### DemoForge-T

Générateur de démo interne OAK-safe. Il transforme un `ProductPlan` et un `SprintPlan` en `DemoPlan` : script, scènes, narration, preuves, checklist OAK, signaux de succès, répétition et export Markdown.

### LaunchForge-T

Générateur de brouillon de lancement interne. Il transforme un `ProductPlan` et un `DemoPlan` en `LaunchDraft` : landing page draft, pitch, audience, canaux privés, actifs de démo, blockers, checklist IP/OAK et export Markdown. Il ne publie rien automatiquement.

### RevenueForge-T

Générateur d'hypothèses de revenus OAK-safe. Il transforme un `ProductPlan` et un `LaunchDraft` en `RevenuePlan` : offres, prix à tester, canaux privés, signaux de revenu, contrôles OAK, ProductBench et prochaines actions. Il ne vend rien et n'envoie rien automatiquement.

### ProductBench-T

Benchmark produit. Il mesure value, clarity, differentiation, feasibility, testability, revenue potential, strategic fit, risk, scope creep et IP uncertainty. Le score est un signal de priorisation, pas une preuve de marché.

### FeedbackLoop-T

Boucle de feedback OAK-safe. Elle transforme un `RevenuePlan` et des `FeedbackSignal` en `FeedbackLoopResult` : score de confiance, décision, prochaine version, M+, M-, contrôles OAK et prochaines actions. Elle ne contacte personne automatiquement.

### VersionForge-T

Planificateur de versions OAK-safe. Il transforme un `FeedbackLoopResult` en `VersionPlan` : version cible, changements, critères de release, blockers, changelog, prochaines actions et export Markdown. Il ne crée pas de tag ni de release automatiquement.

## Structure

```text
omega_game_t/
  docs/
    CIRCUIT_DUNGEON_T.md
    DEMO_FORGE_T.md
    ENERGY_CIVILIZATION_T.md
    FEEDBACK_LOOP_T.md
    GAMEENGINEOS_T.md
    GAMEMASTER_ACADEMY_T.md
    GITHUB_REALM_ENGINE_T.md
    GM_COUNCIL_T.md
    ISSUE_FORGE_T.md
    LAUNCH_FORGE_T.md
    OAKBENCH_GAME_T.md
    OMEGA_GAME_T_MANIFESTO.md
    OMEGA_GAME_T_PLUS_PLUS.md
    OAK_GAME_PROTOCOL.md
    PRODUCT_BENCH_T.md
    PRODUCTIZER_T.md
    REVENUE_FORGE_T.md
    SCIENCE_SANDBOX_T.md
    SPRINT_FORGE_T.md
    THEORY_COMPILER_T.md
    VERSION_FORGE_T.md
  schemas/
    circuit_door.schema.json
    compiled_world.schema.json
    demo_plan.schema.json
    energy_colony.schema.json
    event.schema.json
    feedback_loop.schema.json
    game_engine_state.schema.json
    gamemaster_academy.schema.json
    gm_vote.schema.json
    issue_set.schema.json
    launch_draft.schema.json
    oak_report.schema.json
    oakbench_result.schema.json
    product_bench.schema.json
    product_plan.schema.json
    quest_blueprint.schema.json
    repo_world.schema.json
    revenue_plan.schema.json
    rule_genome.schema.json
    simulation_result.schema.json
    sprint_plan.schema.json
    version_plan.schema.json
    world_dna.schema.json
    world_graph.schema.json
  omega_game/
    bench/
      oakbench_game.py
    engines/
      boardgame.py
      circuit_dungeon.py
      code_dojo.py
      energy_civilization.py
      github_realm.py
      process_alchemy.py
      prototype_world.py
      science_sandbox.py
      textworld.py
    examples/
      boardgame_t_demo.py
      circuit_dungeon_t_demo.py
      demo_forge_t_demo.py
      energy_civilization_t_demo.py
      feedback_loop_t_demo.py
      gameengineos_t_demo.py
      gamemaster_academy_t_demo.py
      github_realm_t_demo.py
      gm_council_t_demo.py
      issue_forge_t_demo.py
      launch_forge_t_demo.py
      oakbench_game_t_demo.py
      product_bench_t_demo.py
      productizer_t_demo.py
      quest_cvcd_demo.py
      revenue_forge_t_demo.py
      science_sandbox_t_demo.py
      sprint_forge_t_demo.py
      theory_compiler_t_demo.py
      version_forge_t_demo.py
    forge/
      demo_forge.py
      feedback_loop.py
      issue_forge.py
      launch_forge.py
      product_bench.py
      revenue_forge.py
      sprint_forge.py
      version_forge.py
    kernel/
      game_kernel.py
      resource_flow.py
      world_state.py
    masters/
      academy.py
    gm_council.py
    productizer.py
    theory_compiler.py
  tests/
    test_boardgame_t.py
    test_circuit_dungeon_t.py
    test_demo_forge_t.py
    test_energy_civilization_t.py
    test_feedback_loop_t.py
    test_gameengineos_t.py
    test_gamemaster_academy_t.py
    test_github_realm_t.py
    test_gm_council_t.py
    test_issue_forge_t.py
    test_launch_forge_t.py
    test_oakbench_game_t.py
    test_omega_game_t.py
    test_product_bench_t.py
    test_productizer_t.py
    test_revenue_forge_t.py
    test_science_sandbox_t.py
    test_sprint_forge_t.py
    test_theory_compiler_t.py
    test_version_forge_t.py
```

## Règle OAK

> Un jeu de Tristan doit maximiser l'émergence, pas l'addiction.

Ω-GAME-T peut entraîner, inspirer, simuler et enseigner, mais il ne doit pas manipuler, radicaliser, exploiter ou tromper.
