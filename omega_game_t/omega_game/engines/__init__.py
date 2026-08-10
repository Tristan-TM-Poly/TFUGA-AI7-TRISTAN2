"""Omega GAME T engine split units."""

from .coevolution import (
    AgentGeneralization,
    CoevolutionReport,
    EnvironmentEvaluation,
    EnvironmentGenome,
    evolve_environments,
    run_coevolution_cycle,
    seed_environments,
)
from .evolution import EvolutionConfig, EvolutionRun, GenerationReport, evolve, evolve_generation, seed_population
from .evolutionary_memory import (
    AntiForgettingReport,
    ChampionRecord,
    EvolutionaryMemory,
    HallOfFame,
    MemoryRecord,
    RegressionResult,
    evaluate_anti_forgetting,
)
from .game_spec import (
    ARENA_ACTION_ALIASES,
    ARENA_ACTIONS,
    GAME_SPEC_VERSION,
    CompiledGame,
    GameAgentSpec,
    GameEnvironmentSpec,
    GameRuleSpec,
    GameSpec,
    GameSpecCompiler,
)
from .integrated_oakbench import (
    CapabilityRecord,
    FaultInjectionResult,
    IntegratedOAKBenchConfig,
    IntegratedOAKBenchReport,
    run_integrated_oakbench,
)
from .layout import ArenaLayout, Coordinate, LayoutAudit, distance_map, shortest_step_candidates, walkable_neighbors
from .language_curriculum import CurriculumProgress, CurriculumQuest, CurriculumTrack, LanguageCurriculum, default_language_curriculum
from .language_dataset_forge import LanguageDataset, LanguageDatasetForge, LanguageDatasetItem, default_language_dataset_forge
from .language_gm_rubric import LanguageGMEvaluation, LanguageGMRubric, LanguageRubricScores
from .language_repair_loop import LanguageRepairLoop, RepairAction, RepairAttempt, RepairLoopResult, default_language_repair_loop
from .language_validators import LanguageValidators, ValidationCheck, ValidationReport, default_language_validators
from .polyglot_language import LanguageQuest, LanguageRun, PolyglotLanguageEngine
from .quality_diversity import (
    ArchiveConfig,
    BehaviorDescriptor,
    EliteRecord,
    MapElitesArchive,
    QualityDiversityExperiment,
    QualityDiversityReport,
    build_map_elites,
    quality_from_rating,
    run_quality_diversity,
)
from .scheduler import (
    CostGraph,
    CostNode,
    DirtyFrontier,
    Dispatch,
    ScheduledEvent,
    SchedulerTickReport,
    SparseBenchmarkReport,
    SparseEventScheduler,
    SystemSpec,
    TemporalLODPolicy,
    TemporalSignal,
    run_sparse_benchmark,
)
from .simulation import AgentGenome, AgentState, ArenaConfig, MatchResult, run_arena_t0
from .tournament import RatingVector, TournamentReport, run_round_robin
from .verification import FuzzFailure, FuzzReport, SimulationAudit, audit_match, fuzz_arena_t0, match_world_graph

__all__ = [
    "AgentGenome", "AgentState", "ArenaConfig", "MatchResult", "run_arena_t0",
    "ArenaLayout", "Coordinate", "LayoutAudit", "distance_map", "walkable_neighbors", "shortest_step_candidates",
    "RatingVector", "TournamentReport", "run_round_robin",
    "EvolutionConfig", "EvolutionRun", "GenerationReport", "evolve", "evolve_generation", "seed_population",
    "EnvironmentGenome", "EnvironmentEvaluation", "AgentGeneralization", "CoevolutionReport", "seed_environments", "run_coevolution_cycle", "evolve_environments",
    "GAME_SPEC_VERSION", "ARENA_ACTIONS", "ARENA_ACTION_ALIASES", "GameAgentSpec", "GameEnvironmentSpec", "GameRuleSpec", "GameSpec", "CompiledGame", "GameSpecCompiler",
    "IntegratedOAKBenchConfig", "IntegratedOAKBenchReport", "FaultInjectionResult", "CapabilityRecord", "run_integrated_oakbench",
    "MemoryRecord", "ChampionRecord", "HallOfFame", "EvolutionaryMemory", "RegressionResult", "AntiForgettingReport", "evaluate_anti_forgetting",
    "ArchiveConfig", "BehaviorDescriptor", "EliteRecord", "MapElitesArchive", "QualityDiversityReport", "QualityDiversityExperiment", "quality_from_rating", "build_map_elites", "run_quality_diversity",
    "SimulationAudit", "FuzzFailure", "FuzzReport", "audit_match", "fuzz_arena_t0", "match_world_graph",
    "TemporalSignal", "TemporalLODPolicy", "SystemSpec", "ScheduledEvent", "DirtyFrontier", "Dispatch", "SchedulerTickReport", "CostNode", "CostGraph", "SparseEventScheduler", "SparseBenchmarkReport", "run_sparse_benchmark",
    "CurriculumProgress", "CurriculumQuest", "CurriculumTrack", "LanguageCurriculum", "default_language_curriculum",
    "LanguageDataset", "LanguageDatasetForge", "LanguageDatasetItem", "default_language_dataset_forge",
    "LanguageGMEvaluation", "LanguageGMRubric", "LanguageQuest", "LanguageRepairLoop", "RepairAction", "RepairAttempt", "RepairLoopResult", "default_language_repair_loop",
    "LanguageRubricScores", "LanguageRun", "LanguageValidators", "ValidationCheck", "ValidationReport", "default_language_validators", "PolyglotLanguageEngine",
]
