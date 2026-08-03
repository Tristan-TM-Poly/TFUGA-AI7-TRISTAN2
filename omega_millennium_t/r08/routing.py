"""Hardened public API for Ω-PROBLEM-ATLAS-T∞ R0.8 evidence routing."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .audit import audit_routing_campaign
from .compiler import compile_routing_campaign as _compile_routing_campaign
from .model import EVENT_RULES, EVENT_SCHEMA, parse_iso8601

RESERVED_EVENT_FIELDS = {
    "routing_delta",
    "category",
    "previous_event_hash",
    "event_hash",
    "truth_probability_delta",
    "mathematical_truth_probability_claimed",
}


def _validate_raw_events(events_json: Path) -> None:
    payload = json.loads(events_json.read_text(encoding="utf-8"))
    if payload.get("schema") != EVENT_SCHEMA:
        raise ValueError(f"{events_json}: unsupported event schema")
    events = payload.get("events")
    if not isinstance(events, list):
        raise ValueError(f"{events_json}: events must be a list")
    previous_time: str | None = None
    for raw in events:
        if not isinstance(raw, dict):
            raise ValueError(f"{events_json}: every event must be an object")
        forbidden = sorted(RESERVED_EVENT_FIELDS & set(raw))
        if forbidden:
            raise ValueError(
                f"{raw.get('event_id', 'unknown')}: reserved routing fields are compiler-owned: {forbidden}"
            )
        occurred_at = parse_iso8601(str(raw.get("occurred_at", "")), "occurred_at")
        if previous_time is not None and occurred_at < previous_time:
            raise ValueError(
                f"{raw.get('event_id', 'unknown')}: event timestamps must be nondecreasing"
            )
        previous_time = occurred_at


def compile_routing_campaign(
    cells_jsonl: str | Path,
    events_json: str | Path,
    output_dir: str | Path,
    *,
    budget: int = 24,
    max_per_problem: int = 2,
) -> dict[str, Any]:
    events_path = Path(events_json)
    _validate_raw_events(events_path)
    return _compile_routing_campaign(
        cells_jsonl,
        events_path,
        output_dir,
        budget=budget,
        max_per_problem=max_per_problem,
    )


__all__ = [
    "EVENT_RULES",
    "EVENT_SCHEMA",
    "audit_routing_campaign",
    "compile_routing_campaign",
]
