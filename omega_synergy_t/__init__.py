"""Ω-SYNERGY-T∞ — review-first synergy and meta-synergy foundry."""
from .discovery import closure_bridges, discover_n_order, discover_pairs, select_portfolio
from .experiments import compile_experiment, counterfactual_twin
from .graph import CreationGraph
from .ledger import ProofLedger, revalidation_status
from .meta import compose_meta_synergies
from .models import (
    Authority,
    Capability,
    CreationDNA,
    EvidenceRecord,
    ExperimentPlan,
    InterfaceContract,
    MetaSynergy,
    Need,
    PRGene,
    ProductHypothesis,
    SynergyCandidate,
    SynergyStage,
    SynergyTensor,
)
from .pr_orchestra import compile_pr_gene, orchestra_manifest, orchestration_waves
from .scanner import ScannerPolicy, ScanResult, scan_repositories
from .scoring import approximate_shapley, build_candidate, decayed_confidence, pair_tensor

__all__ = [
    "Authority", "Capability", "CreationDNA", "CreationGraph", "EvidenceRecord",
    "ExperimentPlan", "InterfaceContract", "MetaSynergy", "Need", "PRGene",
    "ProductHypothesis", "ProofLedger", "ScanResult", "ScannerPolicy",
    "SynergyCandidate", "SynergyStage", "SynergyTensor", "approximate_shapley",
    "build_candidate", "closure_bridges", "compile_experiment", "compile_pr_gene",
    "compose_meta_synergies", "counterfactual_twin", "decayed_confidence",
    "discover_n_order", "discover_pairs", "orchestra_manifest", "orchestration_waves",
    "pair_tensor", "revalidation_status", "scan_repositories", "select_portfolio",
]
