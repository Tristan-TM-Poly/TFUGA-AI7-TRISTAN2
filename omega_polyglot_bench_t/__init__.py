"""Ω-POLYGLOT-BENCH-T: OAK-safe multi-language backend laboratory."""

from .benchmark import benchmark_backends, select_backend
from .reference import vector_affine_python

__all__ = ["benchmark_backends", "select_backend", "vector_affine_python"]
__version__ = "0.1.0"
