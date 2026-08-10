"""Ω-RECYCLE-T∞ R0.1 — OAK-safe circular recovery research package."""

from .models import Component, Hyperedge, Material, RecoveryMode, RecoveryPlan, RecoveryRoute, ResourceGraph, RouteEvaluation
from .optimizer import Candidate, RecoveryOptimizer
from .passport import MaterialPassport
from .scoring import ScoringPolicy, circularity_score, evaluate_route, material_entropy

__all__ = ["Candidate", "Component", "Hyperedge", "Material", "MaterialPassport", "RecoveryMode", "RecoveryOptimizer", "RecoveryPlan", "RecoveryRoute", "ResourceGraph", "RouteEvaluation", "ScoringPolicy", "circularity_score", "evaluate_route", "material_entropy"]
__version__ = "0.1.0"
