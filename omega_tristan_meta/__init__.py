"""Ω Tristan Meta-Compiler v1."""
from .models import Claim, Evidence, Residual, Capability, Receipt, SystemGenome
from .gates import GateResult, claim_scope_gate, meta_stop_gate, role_separation_gate
from .compiler import MetaCompiler, compile_receipt
from .morphogenesis import (
    CausalMemory,
    MemoryEntry,
    MetaMorphogenesisEngine,
    MorphGenome,
    MorphogenesisReceipt,
    RetentionDecision,
)
from .skill_civilization import (
    CONSTITUTION as META_SKILL_CONSTITUTION,
    CrystallizationReceipt,
    MetaImprovementReceipt,
    RegenerationSeed,
    SkillCrystal,
    SkillGenome,
    SkillPlan,
    ablation_report,
    compile_counterfactual_plans,
    crystallize_skill_plan,
    evaluate_meta_improvement,
    generate_residual_skill_candidates,
    meta_depth_decision,
    meta_generalize,
    regeneration_closure,
    regeneration_seed,
    select_minimum_sufficient_plan,
)
from .representation_tournament import (
    COMPETITORS as REPRESENTATION_COMPETITORS,
    FrozenTask,
    RepresentationResult,
    evaluate_representation,
    load_corpus as load_representation_corpus,
    pareto_front as representation_pareto_front,
    run_tournament as run_representation_tournament,
)

__all__ = [
    "Claim", "Evidence", "Residual", "Capability", "Receipt", "SystemGenome",
    "GateResult", "claim_scope_gate", "meta_stop_gate", "role_separation_gate",
    "MetaCompiler", "compile_receipt",
    "MorphGenome", "MemoryEntry", "CausalMemory", "MorphogenesisReceipt",
    "RetentionDecision", "MetaMorphogenesisEngine",
    "META_SKILL_CONSTITUTION", "SkillGenome", "SkillPlan",
    "MetaImprovementReceipt", "SkillCrystal", "CrystallizationReceipt",
    "RegenerationSeed", "meta_generalize", "compile_counterfactual_plans",
    "select_minimum_sufficient_plan", "generate_residual_skill_candidates",
    "ablation_report", "evaluate_meta_improvement", "meta_depth_decision",
    "crystallize_skill_plan", "regeneration_seed", "regeneration_closure",
    "REPRESENTATION_COMPETITORS", "FrozenTask", "RepresentationResult",
    "evaluate_representation", "load_representation_corpus",
    "representation_pareto_front", "run_representation_tournament",
]
