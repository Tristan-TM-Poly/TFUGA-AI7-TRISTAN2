"""Ω-HYDROQUÉBEC-TRISTAN-T∞ public/synthetic research kernel.

This package deliberately excludes operational grid data and control interfaces.
"""
from .models import Evidence, Hyperedge, Node, Scenario
from .synthetic_quebec import build_synthetic_quebec

__all__ = ["Evidence", "Hyperedge", "Node", "Scenario", "build_synthetic_quebec"]
__version__ = "0.1.0"
