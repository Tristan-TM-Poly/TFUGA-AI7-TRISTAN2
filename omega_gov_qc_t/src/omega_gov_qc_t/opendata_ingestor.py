"""Local open-data ingestion helpers for TristanGovGraph Quebec.

No network fetching is performed here. Callers must provide already-authorized
CSV or JSON text and register the source separately.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from io import StringIO
from typing import Any, Dict, List

from .dataset_health import DatasetRecord
from .source_registry import SourceRecord


@dataclass(frozen=True)
class IngestionResult:
    """Result of local ingestion."""

    dataset: DatasetRecord
    warnings: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset": self.dataset.to_dict(),
            "warnings": list(self.warnings),
            "oak_note": "Ingestion reads local authorized text only; it does not validate legal permission by itself.",
        }


class OpenDataIngestor:
    """Dependency-free CSV/JSON parser for authorized local text."""

    def from_csv_text(
        self,
        *,
        dataset_id: str,
        title: str,
        source: SourceRecord,
        csv_text: str,
    ) -> IngestionResult:
        warnings: List[str] = []
        if source.permission != "allowed":
            warnings.append("source_permission_not_allowed")
        if not csv_text.strip():
            warnings.append("empty_csv_text")

        reader = csv.DictReader(StringIO(csv_text.strip()))
        rows = [dict(row) for row in reader]
        fields = list(reader.fieldnames or [])
        if not fields:
            warnings.append("missing_csv_header")
        if not rows:
            warnings.append("no_rows_parsed")

        dataset = DatasetRecord(
            dataset_id=dataset_id,
            title=title,
            source_id=source.source_id,
            format="csv",
            rows=rows,
            fields=fields,
            notes="Parsed from local CSV text.",
        )
        return IngestionResult(dataset=dataset, warnings=warnings)

    def from_json_text(
        self,
        *,
        dataset_id: str,
        title: str,
        source: SourceRecord,
        json_text: str,
    ) -> IngestionResult:
        warnings: List[str] = []
        if source.permission != "allowed":
            warnings.append("source_permission_not_allowed")
        if not json_text.strip():
            warnings.append("empty_json_text")

        try:
            parsed = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON text: {exc}") from exc

        if isinstance(parsed, dict):
            if isinstance(parsed.get("records"), list):
                rows = parsed["records"]
            elif isinstance(parsed.get("data"), list):
                rows = parsed["data"]
            else:
                rows = [parsed]
                warnings.append("json_object_wrapped_as_single_row")
        elif isinstance(parsed, list):
            rows = parsed
        else:
            raise ValueError("JSON must be an object or a list of objects")

        normalized_rows: List[Dict[str, Any]] = []
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                normalized_rows.append({"value": row})
                warnings.append(f"non_object_row_wrapped:{index}")
            else:
                normalized_rows.append(dict(row))

        fields = DatasetRecord.infer_fields(normalized_rows)
        if not normalized_rows:
            warnings.append("no_rows_parsed")
        if not fields:
            warnings.append("no_fields_inferred")

        dataset = DatasetRecord(
            dataset_id=dataset_id,
            title=title,
            source_id=source.source_id,
            format="json",
            rows=normalized_rows,
            fields=fields,
            notes="Parsed from local JSON text.",
        )
        return IngestionResult(dataset=dataset, warnings=warnings)
