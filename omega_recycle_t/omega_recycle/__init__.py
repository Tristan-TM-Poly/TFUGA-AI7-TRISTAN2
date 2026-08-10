"""Ω-RECYCLE-T∞ R0.2 — OAK-safe circular recovery research package."""

from .flows import ConstrainedRecoveryOptimizer, FlowConstraints, GlobalOptimizationResult
from .models import Component, Hyperedge, Material, RecoveryMode, RecoveryPlan, RecoveryRoute, ResourceGraph, RouteEvaluation
from .optimizer import Candidate, RecoveryOptimizer
from .passport import MaterialPassport
from .scoring import ScoringPolicy, circularity_score, evaluate_route, material_entropy
from .symbiosis import MaterialNeed, MaterialOffer, SymbiosisMatch, match_material_flows
from .uncertainty import RouteSwitch, functional_probability_sweep, switching_thresholds
from .urban_mine import StockRecord, aggregate_recoverable_stock

__all__ = ["Candidate", "Component", "ConstrainedRecoveryOptimizer", "FlowConstraints", "GlobalOptimizationResult", "Hyperedge", "Material", "MaterialNeed", "MaterialOffer", "MaterialPassport", "RecoveryMode", "RecoveryOptimizer", "RecoveryPlan", "RecoveryRoute", "ResourceGraph", "RouteEvaluation", "RouteSwitch", "ScoringPolicy", "StockRecord", "SymbiosisMatch", "aggregate_recoverable_stock", "circularity_score", "evaluate_route", "functional_probability_sweep", "match_material_flows", "material_entropy", "switching_thresholds"]
__version__ = "0.2.0"
