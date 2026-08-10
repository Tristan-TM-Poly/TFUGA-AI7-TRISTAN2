"""Ω-RECYCLE-T∞ R0.3 — OAK-safe circular recovery research package."""

from .adapters import UrbanMineAssetRecord, adapt_asset_records, battery_mine_record, building_mine_record, electronics_mine_record
from .baselines import BaselineResult, compare_baselines
from .bayes import BetaFunctionalPosterior, RoutePosteriorSummary, bayesian_route_preferences
from .flows import ConstrainedRecoveryOptimizer, FlowConstraints, GlobalOptimizationResult
from .lca import InventoryFlow, LCAInventory, inventory_for_route
from .models import Component, Hyperedge, Material, RecoveryMode, RecoveryPlan, RecoveryRoute, ResourceGraph, RouteEvaluation
from .optimizer import Candidate, RecoveryOptimizer
from .passport import MaterialPassport
from .provenance import ProvenanceRecord, canonical_dataset_hash, sha256_bytes
from .scalable import BranchAndBoundRecoveryOptimizer, ScalableOptimizationResult, SearchBudget
from .scoring import ScoringPolicy, circularity_score, evaluate_route, material_entropy
from .symbiosis import MaterialNeed, MaterialOffer, SymbiosisMatch, match_material_flows
from .uncertainty import RouteSwitch, functional_probability_sweep, switching_thresholds
from .urban_mine import StockRecord, aggregate_recoverable_stock

__all__ = [
    "BaselineResult", "BetaFunctionalPosterior", "BranchAndBoundRecoveryOptimizer", "Candidate", "Component",
    "ConstrainedRecoveryOptimizer", "FlowConstraints", "GlobalOptimizationResult", "Hyperedge", "InventoryFlow",
    "LCAInventory", "Material", "MaterialNeed", "MaterialOffer", "MaterialPassport", "ProvenanceRecord", "RecoveryMode",
    "RecoveryOptimizer", "RecoveryPlan", "RecoveryRoute", "ResourceGraph", "RouteEvaluation", "RoutePosteriorSummary",
    "RouteSwitch", "ScalableOptimizationResult", "ScoringPolicy", "SearchBudget", "StockRecord", "SymbiosisMatch",
    "UrbanMineAssetRecord", "adapt_asset_records", "aggregate_recoverable_stock", "battery_mine_record",
    "bayesian_route_preferences", "building_mine_record", "canonical_dataset_hash", "circularity_score",
    "compare_baselines", "electronics_mine_record", "evaluate_route", "functional_probability_sweep",
    "inventory_for_route", "match_material_flows", "material_entropy", "sha256_bytes", "switching_thresholds",
]
__version__ = "0.3.0"
