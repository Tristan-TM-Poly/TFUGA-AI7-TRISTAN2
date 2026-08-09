"""Omega GAME T core split.

Small, testable units extracted from the larger GAME branch. The
Ω-GAME-SIM-EVO-T∞ layer extends the merged WorldGraph/OAK core with a
reproducible simulation, tournament, evolution, fuzzing, sparse scheduling,
quality diversity, evolutionary memory, coevolution, bounded GameSpec IR and
hashed fixed layouts.
"""

from .core import Entity, Event, RuleKernel, WorldGraph, GameQualityScore
from .engines import (
    ARENA_ACTION_ALIASES, ARENA_ACTIONS, GAME_SPEC_VERSION,
    AgentGeneralization, AgentGenome, AgentState, AntiForgettingReport,
    ArchiveConfig, ArenaConfig, ArenaLayout, BehaviorDescriptor, ChampionRecord,
    CoevolutionReport, CompiledGame, Coordinate, CostGraph, CostNode,
    CurriculumProgress, CurriculumQuest, CurriculumTrack, DirtyFrontier, Dispatch,
    EliteRecord, EnvironmentEvaluation, EnvironmentGenome, EvolutionConfig,
    EvolutionRun, EvolutionaryMemory, FuzzFailure, FuzzReport, GameAgentSpec,
    GameEnvironmentSpec, GameRuleSpec, GameSpec, GameSpecCompiler, GenerationReport,
    HallOfFame, LanguageCurriculum, LanguageDataset, LanguageDatasetForge,
    LanguageDatasetItem, LanguageGMEvaluation, LanguageGMRubric, LanguageQuest,
    LanguageRepairLoop, LanguageRubricScores, LanguageRun, LanguageValidators,
    LayoutAudit, MapElitesArchive, MatchResult, MemoryRecord, PolyglotLanguageEngine,
    QualityDiversityExperiment, QualityDiversityReport, RatingVector, RegressionResult,
    RepairAction, RepairAttempt, RepairLoopResult, ScheduledEvent, SchedulerTickReport,
    SimulationAudit, SparseBenchmarkReport, SparseEventScheduler, SystemSpec,
    TemporalLODPolicy, TemporalSignal, TournamentReport, ValidationCheck, ValidationReport,
    audit_match, build_map_elites, default_language_curriculum,
    default_language_dataset_forge, default_language_repair_loop,
    default_language_validators, distance_map, evaluate_anti_forgetting, evolve,
    evolve_environments, evolve_generation, fuzz_arena_t0, match_world_graph,
    quality_from_rating, run_arena_t0, run_coevolution_cycle, run_quality_diversity,
    run_round_robin, run_sparse_benchmark, seed_environments, seed_population,
    shortest_step_candidates, walkable_neighbors,
)
from .oak import OAKGate, OAKReport

__all__ = [
    "Entity", "Event", "RuleKernel", "WorldGraph", "GameQualityScore",
    "AgentGenome", "AgentState", "ArenaConfig", "ArenaLayout", "Coordinate", "LayoutAudit",
    "distance_map", "walkable_neighbors", "shortest_step_candidates", "MatchResult", "run_arena_t0",
    "RatingVector", "TournamentReport", "run_round_robin",
    "EvolutionConfig", "EvolutionRun", "GenerationReport", "evolve", "evolve_generation", "seed_population",
    "EnvironmentGenome", "EnvironmentEvaluation", "AgentGeneralization", "CoevolutionReport", "seed_environments", "run_coevolution_cycle", "evolve_environments",
    "GAME_SPEC_VERSION", "ARENA_ACTIONS", "ARENA_ACTION_ALIASES", "GameAgentSpec", "GameEnvironmentSpec", "GameRuleSpec", "GameSpec", "CompiledGame", "GameSpecCompiler",
    "MemoryRecord", "ChampionRecord", "HallOfFame", "EvolutionaryMemory", "RegressionResult", "AntiForgettingReport", "evaluate_anti_forgetting",
    "ArchiveConfig", "BehaviorDescriptor", "EliteRecord", "MapElitesArchive", "QualityDiversityReport", "QualityDiversityExperiment", "quality_from_rating", "build_map_elites", "run_quality_diversity",
    "SimulationAudit", "FuzzFailure", "FuzzReport", "audit_match", "fuzz_arena_t0", "match_world_graph",
    "TemporalSignal", "TemporalLODPolicy", "SystemSpec", "ScheduledEvent", "DirtyFrontier", "Dispatch", "SchedulerTickReport", "CostNode", "CostGraph", "SparseEventScheduler", "SparseBenchmarkReport", "run_sparse_benchmark",
    "CurriculumProgress", "CurriculumQuest", "CurriculumTrack", "LanguageCurriculum", "default_language_curriculum",
    "LanguageDataset", "LanguageDatasetForge", "LanguageDatasetItem", "default_language_dataset_forge",
    "LanguageGMEvaluation", "LanguageGMRubric", "LanguageQuest", "LanguageRepairLoop", "RepairAction", "RepairAttempt", "RepairLoopResult", "default_language_repair_loop",
    "LanguageRubricScores", "LanguageRun", "LanguageValidators", "ValidationCheck", "ValidationReport", "default_language_validators", "PolyglotLanguageEngine",
    "OAKGate", "OAKReport",
]
