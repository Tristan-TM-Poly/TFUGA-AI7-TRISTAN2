"""Ω-SOLID-T∞ executable research kernel.

The package separates established material-science relations, engineering
approximations, exploratory Tristan operators, and experimental evidence.
"""

from .atlas import ARCHETYPE_NAMES, build_archetype, iter_archetypes
from .genome import SolidGenome, load_genome, save_genome
from .hypergraph import SolidHyperGraph
from .oak import OAKReport, run_oak_gate
from .pipeline import SolidPipeline, SolidReport

__all__ = [
    "ARCHETYPE_NAMES",
    "OAKReport",
    "SolidGenome",
    "SolidHyperGraph",
    "SolidPipeline",
    "SolidReport",
    "build_archetype",
    "iter_archetypes",
    "load_genome",
    "run_oak_gate",
    "save_genome",
]

__version__ = "0.1.0"
