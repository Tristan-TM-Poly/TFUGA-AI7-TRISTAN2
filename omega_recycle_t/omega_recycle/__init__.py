"""Ω-RECYCLE-T∞ R0.6 — OAK-safe circular recovery evidence kernel."""

from .adapters import UrbanMineAssetRecord, adapt_asset_records, battery_mine_record, building_mine_record, electronics_mine_record
from .baselines import BaselineResult, compare_baselines
from .bayes import BetaFunctionalPosterior, RoutePosteriorSummary, bayesian_route_preferences
from .calibration import CalibrationReport, ProbabilisticObservation, ReliabilityBin, calibration_report
from .campaign import MethodMetrics, PredictionCampaignReport, PredictionCase, evaluate_prediction_campaign
from .datasets import DatasetSnapshot, EPA_SMM_FACTS_2018, EUROSTAT_ENV_WASMUN, PublicDatasetSpec, ingest_delimited_snapshot, public_dataset_catalog
from .epa import EPASMMObservation, parse_epa_smm_normalized_csv, short_tons_to_metric_tonnes
from .eurostat import EnvWasmunObservation, EurostatObservation, adapt_env_wasmun_tsv, parse_eurostat_tsv
from .flows import ConstrainedRecoveryOptimizer, FlowConstraints, GlobalOptimizationResult
from .general_network import BalanceNode, DirectedAllocation, DirectedArc, GeneralFlowResult, min_cost_general_flow
from .holdout import TemporalHoldoutReport, TemporalPredictionCase, evaluate_temporal_holdout
from .lca import InventoryFlow, LCAInventory, inventory_for_route
from .lcia import CharacterizationFactor, CharacterizationResult, CharacterizationSet, ImpactScore, characterize_inventory
from .lcia_governance import GovernedFactor, GovernedMethod, MethodDescriptor, validate_governed_method
from .live_sources import EPA_SMM_LANDING_LIVE, EUROSTAT_ENV_WASMUN_LIVE, LiveManifestDiff, LiveSnapshot, LiveSourceSpec, compare_live_snapshots, fetch_live_snapshot, render_manifest
from .models import Component, Hyperedge, Material, RecoveryMode, RecoveryPlan, RecoveryRoute, ResourceGraph, RouteEvaluation
from .multi_commodity import Commodity, CommodityAllocation, MultiCommodityResult, SharedArc, solve_fractional_multi_commodity
from .network import DemandNode, SupplyNode, TransferAllocation, TransferArc, TransportResult, min_cost_transport
from .optimizer import Candidate, RecoveryOptimizer
from .passport import MaterialPassport
from .provenance import ProvenanceRecord, canonical_dataset_hash, sha256_bytes
from .revision import RecordRevision, RevisionReport, compare_record_snapshots, structure_hash
from .scalable import BranchAndBoundRecoveryOptimizer, ScalableOptimizationResult, SearchBudget
from .scoring import ScoringPolicy, circularity_score, evaluate_route, material_entropy
from .solver_crosscheck import SolverCrosscheckReport, crosscheck_general_flow, crosscheck_time_expanded_flow, scipy_available
from .source_anchors import EPA_SMM_ANCHOR, EUROSTAT_ENV_WASMUN_ANCHOR, SOURCE_ANCHORS, SourceAnchor
from .symbiosis import MaterialNeed, MaterialOffer, SymbiosisMatch, match_material_flows
from .symbiosis_court import SymbiosisOptimizationResult, SymbiosisRegretReport, exact_match_material_flows, symbiosis_regret
from .temporal_calibration import CalibrationDriftReport, CalibrationWindow, TimedProbabilisticObservation, temporal_calibration_report
from .temporal_network import TemporalArc, TemporalBalance, solve_time_expanded_flow
from .uncertainty import RouteSwitch, functional_probability_sweep, switching_thresholds
from .unit_ontology import UnitDef, compatible_units, convert_value, unit_def
from .urban_mine import StockRecord, aggregate_recoverable_stock

__all__ = [
    "BalanceNode", "BaselineResult", "BetaFunctionalPosterior", "BranchAndBoundRecoveryOptimizer", "CalibrationDriftReport", "CalibrationReport", "CalibrationWindow", "Candidate", "CharacterizationFactor", "CharacterizationResult", "CharacterizationSet", "Commodity", "CommodityAllocation", "Component", "ConstrainedRecoveryOptimizer", "DatasetSnapshot", "DemandNode", "DirectedAllocation", "DirectedArc", "EPASMMObservation", "EPA_SMM_ANCHOR", "EPA_SMM_FACTS_2018", "EPA_SMM_LANDING_LIVE", "EUROSTAT_ENV_WASMUN", "EUROSTAT_ENV_WASMUN_ANCHOR", "EUROSTAT_ENV_WASMUN_LIVE", "EnvWasmunObservation", "EurostatObservation", "FlowConstraints", "GeneralFlowResult", "GlobalOptimizationResult", "GovernedFactor", "GovernedMethod", "Hyperedge", "ImpactScore", "InventoryFlow", "LCAInventory", "LiveManifestDiff", "LiveSnapshot", "LiveSourceSpec", "Material", "MaterialNeed", "MaterialOffer", "MaterialPassport", "MethodDescriptor", "MethodMetrics", "MultiCommodityResult", "PredictionCampaignReport", "PredictionCase", "ProbabilisticObservation", "ProvenanceRecord", "PublicDatasetSpec", "RecordRevision", "RecoveryMode", "RecoveryOptimizer", "RecoveryPlan", "RecoveryRoute", "ReliabilityBin", "ResourceGraph", "RevisionReport", "RouteEvaluation", "RoutePosteriorSummary", "RouteSwitch", "SOURCE_ANCHORS", "ScalableOptimizationResult", "ScoringPolicy", "SearchBudget", "SharedArc", "SolverCrosscheckReport", "SourceAnchor", "StockRecord", "SupplyNode", "SymbiosisMatch", "SymbiosisOptimizationResult", "SymbiosisRegretReport", "TemporalArc", "TemporalBalance", "TemporalHoldoutReport", "TemporalPredictionCase", "TimedProbabilisticObservation", "TransferAllocation", "TransferArc", "TransportResult", "UnitDef", "UrbanMineAssetRecord", "adapt_asset_records", "adapt_env_wasmun_tsv", "aggregate_recoverable_stock", "battery_mine_record", "bayesian_route_preferences", "building_mine_record", "calibration_report", "canonical_dataset_hash", "characterize_inventory", "circularity_score", "compare_baselines", "compare_live_snapshots", "compare_record_snapshots", "compatible_units", "convert_value", "crosscheck_general_flow", "crosscheck_time_expanded_flow", "electronics_mine_record", "evaluate_prediction_campaign", "evaluate_route", "evaluate_temporal_holdout", "exact_match_material_flows", "fetch_live_snapshot", "functional_probability_sweep", "ingest_delimited_snapshot", "inventory_for_route", "match_material_flows", "material_entropy", "min_cost_general_flow", "min_cost_transport", "parse_epa_smm_normalized_csv", "parse_eurostat_tsv", "public_dataset_catalog", "render_manifest", "scipy_available", "sha256_bytes", "short_tons_to_metric_tonnes", "solve_fractional_multi_commodity", "solve_time_expanded_flow", "structure_hash", "switching_thresholds", "symbiosis_regret", "temporal_calibration_report", "unit_def", "validate_governed_method"
]

__version__ = "0.6.0"
