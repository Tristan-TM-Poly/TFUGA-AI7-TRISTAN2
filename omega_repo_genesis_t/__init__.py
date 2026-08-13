"""Ω-REPO-GENESIS-T∞: bounded, private-by-default GitHub repository genesis."""
from .model import RepoSpec, Constellation
from .plan import build_plan, load_constellation

__all__ = ["RepoSpec", "Constellation", "build_plan", "load_constellation"]
__version__ = "0.1.0"
