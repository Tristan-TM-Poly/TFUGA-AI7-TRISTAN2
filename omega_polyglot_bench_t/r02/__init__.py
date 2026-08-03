"""Ω-POLYGLOT-MULTIVERSE-T∞ R0.2 public API."""
from .catalog import generate_catalog
from .campaign import materialize
from .frontier import FrontierAxes, LogicalFrontier
from .generator import generate_affine_source
from .model import AlgorithmSpec, ScoreVector, VariantAddress
from .selector import pareto_front, select_weighted

__all__ = [
    "AlgorithmSpec", "FrontierAxes", "LogicalFrontier", "ScoreVector", "VariantAddress",
    "generate_affine_source", "generate_catalog", "materialize", "pareto_front", "select_weighted",
]
__version__ = "0.2.0"
