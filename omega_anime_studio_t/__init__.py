"""Ω-ANIME-STUDIO-T∞ R1 public API."""

from .compiler import compile_project_bundle
from .eighth_fire import build_eighth_fire_r1
from .frontier import (
    AdaptiveFrontierController, FrontierBudget, FrontierState,
    compile_frontier_sample, iter_scene_variants,
)
from .graph import AnimeGraph
from .matrix import (
    ARTIFACT_KINDS, DOMAINS, iter_matrix_cells, matrix_summary,
    validate_matrix, write_matrix_jsonl,
)
from .models import *

__all__ = [
    'AdaptiveFrontierController','AnimeGraph','ARTIFACT_KINDS','DOMAINS',
    'FrontierBudget','FrontierState','build_eighth_fire_r1',
    'compile_frontier_sample','compile_project_bundle','iter_matrix_cells',
    'iter_scene_variants','matrix_summary','validate_matrix','write_matrix_jsonl',
]
__version__ = '1.0.0'
