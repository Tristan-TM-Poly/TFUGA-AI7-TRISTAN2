"""Ω-SOLID-T∞ R0.2 — Solid Universe Compiler.

OAK-safe research infrastructure for representing, generating, validating and
indexing solid-material candidates. Generated candidates are not certified
materials, experimental discoveries, safety claims, or fabrication recipes.
"""
from .models import (
    CandidateCell, EvidenceRef, OAKFinding, OAKReport, Quantity,
    SolidGenomeR2, U2Tensor,
)
from .campaign import CampaignSpec, default_campaign_spec
from .mixed_radix import MixedRadixSpace
from .oak import evaluate_candidate

__all__ = [
    "CandidateCell", "EvidenceRef", "OAKFinding", "OAKReport", "Quantity",
    "SolidGenomeR2", "U2Tensor", "CampaignSpec", "default_campaign_spec",
    "MixedRadixSpace", "evaluate_candidate",
]
__version__ = "0.2.0"
