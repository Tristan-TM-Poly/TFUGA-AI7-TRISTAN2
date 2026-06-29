"""Adapter router for Omega absorb v1.6."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

from .local_json_loader import normalize_local_json_records


@dataclass(frozen=True)
class AdapterRoute:
    source_id: str
    adapter_name: str
    confidence: float
    reasons: Tuple[str, ...]
    next_action: str


@dataclass(frozen=True)
class RoutedRecords:
    route: AdapterRoute
    records: Tuple[Dict[str, object], ...]
    normalized_records: Tuple[Dict[str, object], ...]
    next_action: str


def detect_source_family(record: Dict[str, object]) -> AdapterRoute:
    keys = {str(key).lower() for key in record.keys()}
    if {"dc.title", "dc.creator"} & keys or "division" in keys:
        return AdapterRoute(
            source_id="polypublie",
            adapter_name="PolyPublieLikeAdapter",
            confidence=0.86,
            reasons=("bibliographic_metadata_keys",),
            next_action="normalize_with_polypublie_adapter",
        )
    if "expertise" in keys or "department" in keys or "name" in keys:
        return AdapterRoute(
            source_id="expertise",
            adapter_name="ExpertiseLikeAdapter",
            confidence=0.82,
            reasons=("profile_or_expertise_keys",),
            next_action="normalize_with_expertise_adapter",
        )
    return AdapterRoute(
        source_id="generic",
        adapter_name="GenericPublicMetadataAdapter",
        confidence=0.55,
        reasons=("fallback_generic_metadata",),
        next_action="normalize_with_generic_adapter",
    )


def route_records(records: Iterable[Dict[str, object]], preferred_source: str | None = None) -> RoutedRecords:
    records_tuple = tuple(records)
    if preferred_source:
        source = preferred_source.strip().lower()
        adapter = {
            "polypublie": "PolyPublieLikeAdapter",
            "expertise": "ExpertiseLikeAdapter",
            "generic": "GenericPublicMetadataAdapter",
        }.get(source, "GenericPublicMetadataAdapter")
        route = AdapterRoute(source, adapter, 1.0, ("preferred_source",), f"normalize_with_{source}_adapter")
    elif records_tuple:
        route = detect_source_family(records_tuple[0])
    else:
        route = AdapterRoute("generic", "GenericPublicMetadataAdapter", 0.0, ("empty_records",), "collect_records")
    normalized = normalize_local_json_records(records_tuple, route.source_id)
    return RoutedRecords(
        route=route,
        records=records_tuple,
        normalized_records=normalized,
        next_action="apply_source_oak_policy",
    )
