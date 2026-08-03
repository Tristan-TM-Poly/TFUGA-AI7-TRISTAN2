"""Ω-GITHUB-REVENUE-T∞ / OAKSponsorOS-T.

Evidence-bearing, privacy-safe primitives for turning GitHub research artifacts
into reviewable sponsorship, service, product, and licensing candidates.
"""

from .engine import (
    allocate_capital,
    assess_sponsor_tier,
    compile_offer,
    decide_experiment,
    evaluate_artifact,
    stream_frontier,
)
from .ledger import AppendOnlyLedger, SensitiveDataError
from .models import (
    Artifact,
    DisclosureClass,
    Evidence,
    Experiment,
    ExperimentDecision,
    OAKStatus,
    Offer,
    RevenueEvent,
    RevenuePath,
    SponsorTier,
)

__all__ = [
    "allocate_capital",
    "assess_sponsor_tier",
    "compile_offer",
    "decide_experiment",
    "evaluate_artifact",
    "stream_frontier",
    "AppendOnlyLedger",
    "SensitiveDataError",
    "Artifact",
    "DisclosureClass",
    "Evidence",
    "Experiment",
    "ExperimentDecision",
    "OAKStatus",
    "Offer",
    "RevenueEvent",
    "RevenuePath",
    "SponsorTier",
]

__version__ = "0.1.0"
