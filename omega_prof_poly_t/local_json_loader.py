"""Local JSON loader for Omega absorb v1.3."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

from .poly_public_adapters import ExpertiseLikeAdapter, PolyPublieLikeAdapter
from .public_metadata_adapters import GenericPublicMetadataAdapter


@dataclass(frozen=True)
class LocalJSONLoadResult:
    path: str
    source: str
    records: Tuple[Dict[str, object], ...]
    normalized_records: Tuple[Dict[str, object], ...]
    next_action: str


def load_local_json_records(path: str | Path) -> Tuple[Dict[str, object], ...]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return (data,)
    if isinstance(data, list):
        return tuple(item for item in data if isinstance(item, dict))
    raise ValueError("local JSON must contain an object or a list of objects")


def normalize_local_json_records(records: Tuple[Dict[str, object], ...], source: str = "generic") -> Tuple[Dict[str, object], ...]:
    source = source.strip().lower()
    if source in {"polypublie", "polypublie_like"}:
        return PolyPublieLikeAdapter().normalize(records)
    if source in {"expertise", "expertise_like"}:
        return ExpertiseLikeAdapter().normalize(records)
    return GenericPublicMetadataAdapter().normalize(records)


def load_and_normalize_local_json(path: str | Path, source: str = "generic") -> LocalJSONLoadResult:
    records = load_local_json_records(path)
    normalized = normalize_local_json_records(records, source)
    return LocalJSONLoadResult(
        path=str(path),
        source=source,
        records=records,
        normalized_records=normalized,
        next_action="route_normalized_records_to_absorption_pipeline",
    )
