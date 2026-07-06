"""Dataset health primitives for TristanGovGraph Quebec.

This module computes conservative data-quality signals. A health report is a
review aid, not a final judgment about a public body or service.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Literal, Sequence

DatasetFormat = Literal["csv", "json", "unknown"]
HealthBand = Literal["good", "review", "poor", "blocked"]


@dataclass(frozen=True)
class DatasetRecord:
    """A local, already-authorized dataset representation."""

    dataset_id: str
    title: str
    source_id: str
    format: DatasetFormat
    rows: List[Dict[str, Any]] = field(default_factory=list)
    fields: List[str] = field(default_factory=list)
    retrieved_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not self.dataset_id.strip():
            errors.append("dataset_id is required")
        if not self.title.strip():
            errors.append("title is required")
        if not self.source_id.strip():
            errors.append("source_id is required")
        if self.format not in DatasetFormat.__args__:  # type: ignore[attr-defined]
            errors.append(f"invalid format: {self.format}")
        return errors

    @property
    def row_count(self) -> int:
        return len(self.rows)

    @property
    def field_count(self) -> int:
        return len(self.fields or self.infer_fields(self.rows))

    @property
    def fingerprint(self) -> str:
        payload = f"{self.dataset_id}|{self.title}|{self.source_id}|{self.format}|{self.row_count}|{self.field_count}"
        return sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def infer_fields(rows: Sequence[Dict[str, Any]]) -> List[str]:
        fields: List[str] = []
        seen = set()
        for row in rows:
            for key in row.keys():
                if key not in seen:
                    seen.add(key)
                    fields.append(key)
        return fields

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "title": self.title,
            "source_id": self.source_id,
            "format": self.format,
            "row_count": self.row_count,
            "field_count": self.field_count,
            "fields": list(self.fields or self.infer_fields(self.rows)),
            "retrieved_at": self.retrieved_at,
            "fingerprint": self.fingerprint,
            "notes": self.notes,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class DatasetHealthReport:
    """Conservative health signals for a dataset."""

    dataset_id: str
    row_count: int
    field_count: int
    missing_cell_count: int
    total_cell_count: int
    duplicate_row_count: int
    machine_readable: bool
    metadata_fields_present: List[str] = field(default_factory=list)
    notes: str = ""

    @property
    def missing_ratio(self) -> float:
        if self.total_cell_count == 0:
            return 1.0
        return self.missing_cell_count / self.total_cell_count

    @property
    def duplicate_ratio(self) -> float:
        if self.row_count == 0:
            return 0.0
        return self.duplicate_row_count / self.row_count

    @property
    def metadata_quality(self) -> float:
        expected = {"title", "source_id", "retrieved_at", "format"}
        if not expected:
            return 1.0
        return len(set(self.metadata_fields_present) & expected) / len(expected)

    @property
    def band(self) -> HealthBand:
        if not self.machine_readable or self.row_count == 0 or self.field_count == 0:
            return "blocked"
        if self.missing_ratio > 0.5:
            return "poor"
        if self.missing_ratio > 0.2 or self.duplicate_ratio > 0.2 or self.metadata_quality < 0.75:
            return "review"
        return "good"

    @property
    def oak_ready(self) -> bool:
        return self.band in {"good", "review"}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "row_count": self.row_count,
            "field_count": self.field_count,
            "missing_cell_count": self.missing_cell_count,
            "total_cell_count": self.total_cell_count,
            "missing_ratio": self.missing_ratio,
            "duplicate_row_count": self.duplicate_row_count,
            "duplicate_ratio": self.duplicate_ratio,
            "machine_readable": self.machine_readable,
            "metadata_quality": self.metadata_quality,
            "metadata_fields_present": list(self.metadata_fields_present),
            "band": self.band,
            "oak_ready": self.oak_ready,
            "notes": self.notes,
            "oak_note": "Dataset health is a signal for review, not a final judgment.",
        }


class DatasetHealthEngine:
    """Evaluate dataset readiness from local rows only."""

    def evaluate(self, dataset: DatasetRecord) -> DatasetHealthReport:
        errors = dataset.validate()
        if errors:
            raise ValueError("Invalid DatasetRecord: " + "; ".join(errors))

        fields = dataset.fields or DatasetRecord.infer_fields(dataset.rows)
        total = len(dataset.rows) * len(fields)
        missing = 0
        normalized_rows: List[str] = []
        for row in dataset.rows:
            normalized_rows.append(str(sorted(row.items())))
            for field_name in fields:
                value = row.get(field_name)
                if value is None or value == "":
                    missing += 1
        duplicate_count = len(normalized_rows) - len(set(normalized_rows))
        metadata_fields_present = [
            field_name
            for field_name in ["title", "source_id", "retrieved_at", "format"]
            if getattr(dataset, field_name, None)
        ]

        return DatasetHealthReport(
            dataset_id=dataset.dataset_id,
            row_count=dataset.row_count,
            field_count=len(fields),
            missing_cell_count=missing,
            total_cell_count=total,
            duplicate_row_count=max(0, duplicate_count),
            machine_readable=dataset.format in {"csv", "json"},
            metadata_fields_present=metadata_fields_present,
            notes=dataset.notes,
        )

    def evaluate_many(self, datasets: Iterable[DatasetRecord]) -> Dict[str, Any]:
        reports = [self.evaluate(dataset) for dataset in datasets]
        return {
            "schema": "omega_gov_qc_t.dataset_health_bundle.v0",
            "reports": [report.to_dict() for report in reports],
            "blocked": [report.dataset_id for report in reports if report.band == "blocked"],
            "review": [report.dataset_id for report in reports if report.band == "review"],
            "good": [report.dataset_id for report in reports if report.band == "good"],
        }
