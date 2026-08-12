"""Ω-COGNITIVE-COMPUTER-T∞ — executable cognitive operator substrate.

The package encodes inspectable problem-solving operators. It deliberately separates
hypothesis generation from evidence, simulation, proof, benchmark and crystallization.
"""

from .algebra import CommutatorReport, commutator, compose, dual_program, idempotence_distance
from .assembly import AssemblyError, parse_assembly, render_assembly
from .cir import CognitiveState, EvidenceItem
from .compiler import CognitiveCompiler, ProblemFingerprint, fingerprint_problem
from .computer import CognitiveComputer
from .crystallization import ArtifactType, CrystallizationRecord, CrystallizationReport, validate_crystallization
from .evolution import CognitiveEvolution, EvolutionCandidate
from .isa import Instruction, Opcode, OperatorRegistry, OperatorSpec, Program, default_registry
from .market import RepresentationAccount, RepresentationMarket
from .memory import CognitiveMemory, MemoryRecord
from .profiler import ablation_profile, discover_meta_skills, pairwise_synergy, shapley_by_instruction
from .runtime import CognitiveRuntime, CognitiveTransaction, ExecutionResult, RuntimeContext
from .superinstructions import SUPERINSTRUCTIONS, TRISTAN_ATTACK, TRISTAN_COMPRESS, TRISTAN_CRYSTALLIZE, TRISTAN_DISCOVER, TRISTAN_EXPLORE

__version__ = "0.1.0"

__all__ = [
    "AssemblyError", "ArtifactType", "CognitiveCompiler", "CognitiveComputer", "CognitiveEvolution",
    "CognitiveMemory", "CognitiveRuntime", "CognitiveState", "CognitiveTransaction", "CommutatorReport",
    "CrystallizationRecord", "CrystallizationReport", "EvidenceItem", "EvolutionCandidate", "ExecutionResult",
    "Instruction", "MemoryRecord", "Opcode", "OperatorRegistry", "OperatorSpec", "ProblemFingerprint", "Program",
    "RepresentationAccount", "RepresentationMarket", "RuntimeContext", "SUPERINSTRUCTIONS", "TRISTAN_ATTACK",
    "TRISTAN_COMPRESS", "TRISTAN_CRYSTALLIZE", "TRISTAN_DISCOVER", "TRISTAN_EXPLORE", "ablation_profile",
    "commutator", "compose", "default_registry", "discover_meta_skills", "dual_program", "fingerprint_problem",
    "idempotence_distance", "pairwise_synergy", "parse_assembly", "render_assembly", "shapley_by_instruction",
    "validate_crystallization",
]
