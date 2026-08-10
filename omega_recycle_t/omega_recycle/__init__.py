"""Ω-RECYCLE-T∞ R0.4 — OAK-safe circular recovery evidence kernel."""

from .adapters import UrbanMineAssetRecord, adapt_asset_records, battery_mine_record, building_mine_record, electronics_mine_record
from .baselines import BaselineResult, compare_baselines
from .bayes import BetaFunctionalPosterior, RoutePosteriorSummary, bayesian_route_preferences
from .calibration import CalibrationReport, ProbabilisticObservation, ReliabilityBin, calibration_report
from .datasets import DatasetSnapshot, EPA_SMM_FACTS_2018, EUROSTAT_ENV_WASMUN, PublicDatasetSpec, ingest_delimited_snapshot, public_dataset_catalog
from .flows import ConstrainedRecoveryOptimizer, FlowConstraints, GlobalOptimizationResult
from .lca import InventoryFlow, LCAInventory, inventory_for_route
from .lcia import CharacterizationFactor, CharacterizationResult, CharacterizationSet, ImpactScore, characterize_inventory
from .models import Component, Hyperedge, Material, RecoveryMode, RecoveryPlan, RecoveryRoute, ResourceGraph, RouteEvaluation
from .network import DemandNode, SupplyNode, TransferAllocation, TransferArc, TransportResult, min_cost_transport
from .optimizer import Candidate, RecoveryOptimizer
from .passport import MaterialPassport
from .provenance import ProvenanceRecord, canonical_dataset_hash, sha256_bytes
from .scalable import BranchAndBoundRecoveryOptimizer, ScalableOptimizationResult, SearchBudget
from .scoring import ScoringPolicy, circularity_score, evaluate_route, material_entropy
from .symbiosis import MaterialNeed, MaterialOffer, SymbiosisMatch, match_material_flows
from .symbiosis_court import SymbiosisOptimizationResult, SymbiosisRegretReport, exact_match_material_flows, symbiosis_regret
from .uncertainty import RouteSwitch, functional_probability_sweep, switching_thresholds
from .urban_mine import StockRecord, aggregate_recoverable_stock

__all__ = [
    "BaselineResult", "BetaFunctionalPosterior", "BranchAndBoundRecoveryOptimizer", "CalibrationReport", "Candidate",
    "CharacterizationFactor", "CharacterizationResult", "CharacterizationSet", "Component", "ConstrainedRecoveryOptimizer",
    "DatasetSnapshot", "DemandNode", "EPA_SMM_FACTS_2018", "EUROSTAT_ENV_WASMUN", "FlowConstraints",
    "GlobalOptimizationResult", "Hyperedge", "ImpactScore", "InventoryFlow", "LCAInventory", "Material", "MaterialNeed",
    "MaterialOffer", "MaterialPassport", "ProbabilisticObservation", "ProvenanceRecord", "PublicDatasetSpec", "RecoveryMode",
    "RecoveryOptimizer", "RecoveryPlan", "RecoveryRoute", "ReliabilityBin", "ResourceGraph", "RouteEvaluation",
    "RoutePosteriorSummary", "RouteSwitch", "ScalableOptimizationResult", "ScoringPolicy", "SearchBudget", "StockRecord",
    "SupplyNode", "SymbiosisMatch", "SymbiosisOptimizationResult", "SymbiosisRegretReport", "TransferAllocation",
    "TransferArc", "TransportResult", "UrbanMineAssetRecord", "adapt_asset_records", "aggregate_recoverable_stock",
    "battery_mine_record", "bayesian_route_preferences", "building_mine_record", "calibration_report",
    "canonical_dataset_hash", "characterize_inventory", "circularity_score", "compare_baselines", "electronics_mine_record",
    "evaluate_route", "exact_match_material_flows", "functional_probability_sweep", "ingest_delimited_snapshot",
    "inventory_for_route", "match_material_flows", "material_entropy", "min_cost_transport", "public_dataset_catalog",
    "sha256_bytes", "switching_thresholds", "symbiosis_regret",
]
__version__ = "0.4.0"
