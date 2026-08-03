"""Streaming materialization of catalogs and logical research cells.

Materialization is bounded by a campaign receipt, never by a permanent global
constant.  The logical address space remains available even when only a small
or medium finite slice is written to disk.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import time
from typing import Any, Callable, Iterable, Iterator, Mapping, TextIO

from .address import CellSpace, iter_addresses
from .catalog import catalog_payload, iter_catalog_records
from .models import CampaignBudget, CellAddress


@dataclass(frozen=True)
class MaterializationStats:
    record_count: int
    byte_count: int
    line_count: int
    elapsed_seconds: float
    sha256: str
    stop_reason: str
    output_path: str

    def to_dict(self) -> dict[str, object]:
        return {
            "record_count": self.record_count,
            "byte_count": self.byte_count,
            "line_count": self.line_count,
            "elapsed_seconds": self.elapsed_seconds,
            "sha256": self.sha256,
            "stop_reason": self.stop_reason,
            "output_path": self.output_path,
        }


class BudgetGuard:
    def __init__(self, budget: CampaignBudget) -> None:
        self.budget = budget
        self.started = time.monotonic()
        self.records = 0
        self.bytes = 0
        self.compute_units = 0

    @property
    def elapsed(self) -> float:
        return time.monotonic() - self.started

    def check(self, *, next_bytes: int = 0, next_compute: int = 1) -> str | None:
        if self.budget.wall_time_seconds is not None and self.elapsed >= self.budget.wall_time_seconds:
            return "wall_time_budget"
        if self.budget.storage_megabytes is not None:
            storage_limit = self.budget.storage_megabytes * 1024 * 1024
            if self.bytes + next_bytes > storage_limit:
                return "storage_budget"
        if self.budget.compute_units is not None and self.compute_units + next_compute > self.budget.compute_units:
            return "compute_budget"
        if self.budget.materialized_cell_cap is not None and self.records >= self.budget.materialized_cell_cap:
            return "campaign_materialized_cell_cap"
        return None

    def consume(self, byte_count: int, compute_units: int = 1) -> None:
        self.records += 1
        self.bytes += byte_count
        self.compute_units += compute_units


def _write_jsonl(
    records: Iterable[Mapping[str, Any]],
    output: Path,
    budget: CampaignBudget,
) -> MaterializationStats:
    output.parent.mkdir(parents=True, exist_ok=True)
    guard = BudgetGuard(budget)
    hasher = sha256()
    stop_reason = "source_exhausted"
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            encoded = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
            byte_count = len(encoded.encode("utf-8"))
            reason = guard.check(next_bytes=byte_count)
            if reason is not None:
                stop_reason = reason
                break
            handle.write(encoded)
            hasher.update(encoded.encode("utf-8"))
            guard.consume(byte_count)
    return MaterializationStats(
        record_count=guard.records,
        byte_count=guard.bytes,
        line_count=guard.records,
        elapsed_seconds=guard.elapsed,
        sha256=hasher.hexdigest(),
        stop_reason=stop_reason,
        output_path=str(output),
    )


def materialize_catalog(
    output: str | Path,
    *,
    budget: CampaignBudget | None = None,
) -> MaterializationStats:
    budget = budget or CampaignBudget()
    return _write_jsonl(iter_catalog_records(), Path(output), budget)


def cell_record(address: CellAddress, *, space: CellSpace, catalog_digest: str) -> dict[str, object]:
    flat = space.flatten(address)
    return {
        "schema": "omega-sequence-forms-cell/1",
        "address": address.render(),
        "flat_index": flat,
        "family_index": address.family,
        "transformation_index": address.transformation,
        "validator_index": address.validator,
        "regime_index": address.regime,
        "domain_index": address.domain,
        "catalog_digest": catalog_digest,
        "status": "unexecuted_research_cell",
        "global_identity_proved": False,
    }


def iter_cell_records(
    *,
    seed: int = 0,
    space: CellSpace | None = None,
) -> Iterator[dict[str, object]]:
    space = space or CellSpace()
    digest = str(catalog_payload()["catalog_digest"])
    for address in iter_addresses(space=space, seed=seed):
        yield cell_record(address, space=space, catalog_digest=digest)


def materialize_cells(
    output: str | Path,
    *,
    seed: int = 0,
    space: CellSpace | None = None,
    budget: CampaignBudget | None = None,
) -> MaterializationStats:
    budget = budget or CampaignBudget(materialized_cell_cap=100_000)
    return _write_jsonl(iter_cell_records(seed=seed, space=space), Path(output), budget)


def materialization_receipt(
    *,
    catalog_stats: MaterializationStats | None = None,
    cell_stats: MaterializationStats | None = None,
    budget: CampaignBudget,
    seed: int,
    space: CellSpace | None = None,
) -> dict[str, object]:
    space = space or CellSpace()
    payload = {
        "schema": "omega-sequence-forms-materialization-receipt/1",
        "catalog": None if catalog_stats is None else catalog_stats.to_dict(),
        "cells": None if cell_stats is None else cell_stats.to_dict(),
        "budget": budget.to_dict(),
        "seed": seed,
        "logical_cells": space.logical_cells,
        "materialized_cells": 0 if cell_stats is None else cell_stats.record_count,
        "permanent_total_cap": None,
        "global_identity_proved": False,
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    payload["receipt_digest"] = sha256(canonical.encode("utf-8")).hexdigest()
    return payload
