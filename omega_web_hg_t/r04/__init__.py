"""Ω-WEB-HG-T∞ R0.4 — authoritative-source planning and MAX metadata absorption."""

from .catalog import BEST_SITES_V1, by_id
from .max_adapters import MAX_ADAPTERS, Adapter, adapter_by_id
from .max_campaign import HttpResponse, run_max_campaign
from .max_sharding import (
    aggregate_shards,
    build_shard_matrix,
    select_adapter_shard,
    shard_for_source,
)
from .models import CampaignPlan, SourceProfile, audit_profiles
from .planner import PlannerOptions, build_plan, materialize_plan

__all__ = [
    "Adapter",
    "BEST_SITES_V1",
    "CampaignPlan",
    "HttpResponse",
    "MAX_ADAPTERS",
    "PlannerOptions",
    "SourceProfile",
    "adapter_by_id",
    "aggregate_shards",
    "audit_profiles",
    "build_plan",
    "build_shard_matrix",
    "by_id",
    "materialize_plan",
    "run_max_campaign",
    "select_adapter_shard",
    "shard_for_source",
]
