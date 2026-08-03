from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .models import ObservationView


class ReceiptError(ValueError):
    pass


def normalize_receipts(
    receipts: Iterable[Mapping[str, Any]],
) -> tuple[tuple[ObservationView, ...], int]:
    observations: list[ObservationView] = []
    logical_frontier = 0
    for receipt_index, receipt in enumerate(receipts):
        campaign_id = str(receipt.get("campaign_id", f"receipt-{receipt_index}"))
        logical_frontier = max(
            logical_frontier,
            _nonnegative_int(receipt.get("logical_frontier_cells", 0), "logical_frontier_cells"),
        )
        raw_observations = receipt.get("observations", ())
        if not isinstance(raw_observations, (list, tuple)):
            raise ReceiptError("observations must be a list or tuple")
        for index, raw in enumerate(raw_observations):
            if not isinstance(raw, Mapping):
                raise ReceiptError(f"observation {index} must be an object")
            cell = raw.get("cell", {})
            if not isinstance(cell, Mapping):
                raise ReceiptError(f"observation {index}.cell must be an object")
            address = str(cell.get("address") or _address_from_cell(cell))
            signatures = raw.get("failure_signatures", ())
            if not isinstance(signatures, (list, tuple)):
                raise ReceiptError("failure_signatures must be a list or tuple")
            observations.append(
                ObservationView(
                    campaign_id=campaign_id,
                    address=address,
                    task_id=str(raw.get("task_id", f"task-{receipt_index}-{index}")),
                    domain=str(cell.get("domain", "unknown")),
                    archetype=str(cell.get("archetype", "unknown")),
                    language=str(cell.get("language", "unknown")),
                    mutation_family=str(cell.get("mutation_family", "unknown")),
                    success=bool(raw.get("success", False)),
                    novelty=_unit_float(raw.get("novelty", 0.0), "novelty"),
                    mutation_score=_unit_float(
                        raw.get("mutation_score", 0.0), "mutation_score"
                    ),
                    information_gain=_unit_float(
                        raw.get("information_gain", 0.0), "information_gain"
                    ),
                    cost_units=max(1, _nonnegative_int(raw.get("cost_units", 1), "cost_units")),
                    failure_signatures=tuple(sorted({str(item) for item in signatures})),
                )
            )
    return tuple(observations), logical_frontier


def _address_from_cell(cell: Mapping[str, Any]) -> str:
    return "/".join(
        str(cell.get(key, "unknown"))
        for key in (
            "domain",
            "archetype",
            "difficulty_band",
            "language",
            "execution_regime",
            "mutation_family",
        )
    )


def _unit_float(value: Any, name: str) -> float:
    number = float(value)
    if not 0.0 <= number <= 1.0:
        raise ReceiptError(f"{name} must be in [0, 1]")
    return number


def _nonnegative_int(value: Any, name: str) -> int:
    number = int(value)
    if number < 0:
        raise ReceiptError(f"{name} must be nonnegative")
    return number
