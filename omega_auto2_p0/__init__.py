"""Omega AUTO2 P0 integration spine.

Composable offline foundation connecting the P0 gateway, usage-event, and
spectral-core modules under one OAK-safe package namespace.
"""

from .oak import OAKEnvelope, combine_oak_status
from .pipeline import run_p0_pipeline

__all__ = ["OAKEnvelope", "combine_oak_status", "run_p0_pipeline"]
