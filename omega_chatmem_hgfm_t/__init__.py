"""Ω-CHATMEM-HGFM-T∞: OAK-safe external memory compiler for ChatGPT conversations."""

from .core import PipelineResult, recall, run_pipeline

__all__ = ["PipelineResult", "recall", "run_pipeline"]
__version__ = "0.1.0"
