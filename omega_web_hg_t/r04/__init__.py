"""Ω-WEB-HG-T∞ R0.4 — authoritative-source campaign planning."""

from .catalog import BEST_SITES_V1, by_id
from .models import CampaignPlan, SourceProfile, audit_profiles
from .planner import PlannerOptions, build_plan, materialize_plan

__all__ = [
    "BEST_SITES_V1",
    "CampaignPlan",
    "PlannerOptions",
    "SourceProfile",
    "audit_profiles",
    "build_plan",
    "by_id",
    "materialize_plan",
]
