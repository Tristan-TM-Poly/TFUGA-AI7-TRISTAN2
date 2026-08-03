from __future__ import annotations
import csv, io, json
from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from typing import Any, Mapping, Sequence
from .foundations import (IngestReceipt, Observation, PublicEvidencePolicy, QuarantineRecord, SourceDescriptor, evaluate_licence, inspect_prohibited_fields, merkle_root, sha256)


# --- validation ---
REQUIRED_FIELDS = (
    "source_id",
    "variable",
    "value",
    "unit",
    "observed_at",
    "region_id",
)

ALLOWED_QUALITY_FLAGS = {"measured_public", "estimated_public", "synthetic_fixture"}

ALLOWED_UNITS = {"MW", "MWh", "%", "index", "count", "hours", "degC"}

def validate_record(record: Mapping[str, Any], policy: PublicEvidencePolicy) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in record or record[field] in (None, ""):
            errors.append(f"MISSING_{field.upper()}")
    prohibited = inspect_prohibited_fields(record, policy)
    errors.extend(f"PROHIBITED_FIELD_{field.upper()}" for field in prohibited)
    try:
        value = float(record.get("value"))
        if not isfinite(value):
            errors.append("NON_FINITE_VALUE")
    except (TypeError, ValueError):
        errors.append("INVALID_NUMERIC_VALUE")
    uncertainty = record.get("uncertainty", 0.0)
    try:
        uncertainty_value = float(uncertainty)
        if not isfinite(uncertainty_value) or uncertainty_value < 0:
            errors.append("INVALID_UNCERTAINTY")
    except (TypeError, ValueError):
        errors.append("INVALID_UNCERTAINTY")
    unit = record.get("unit")
    if unit not in ALLOWED_UNITS:
        errors.append("UNIT_NOT_ALLOWLISTED")
    flag = record.get("quality_flag", "synthetic_fixture")
    if flag not in ALLOWED_QUALITY_FLAGS:
        errors.append("QUALITY_FLAG_NOT_ALLOWLISTED")
    observed_at = record.get("observed_at")
    if observed_at:
        try:
            datetime.fromisoformat(str(observed_at).replace("Z", "+00:00"))
        except ValueError:
            errors.append("INVALID_TIMESTAMP")
    return sorted(set(errors))


# --- quarantine ---
def quarantine(row_number: int, reasons: Sequence[str], record: Mapping[str, Any]) -> QuarantineRecord:
    return QuarantineRecord(
        row_number=row_number,
        reason_codes=tuple(sorted(set(reasons))),
        raw_record=dict(record),
        record_hash=sha256({"row": row_number, "record": record, "reasons": sorted(set(reasons))}),
    )


# --- ingest ---
@dataclass(frozen=True)
class IngestResult:
    observations: Sequence[Observation]
    quarantine: Sequence[QuarantineRecord]
    receipt: IngestReceipt

def _parse_text(text: str, input_format: str) -> list[Mapping[str, Any]]:
    if input_format == "json":
        payload = json.loads(text)
        if isinstance(payload, list):
            return [dict(item) for item in payload]
        if isinstance(payload, dict) and isinstance(payload.get("records"), list):
            return [dict(item) for item in payload["records"]]
        raise ValueError("JSON input must be a list or an object containing records[].")
    if input_format == "jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    if input_format == "csv":
        return [dict(row) for row in csv.DictReader(io.StringIO(text))]
    raise ValueError(f"Unsupported format: {input_format}")

def _normalize(record: Mapping[str, Any], source: SourceDescriptor, row_number: int) -> dict[str, Any]:
    normalized = dict(record)
    normalized.setdefault("source_id", source.source_id)
    normalized.setdefault("quality_flag", "synthetic_fixture" if source.source_kind == "synthetic_fixture" else "estimated_public")
    normalized.setdefault("uncertainty", 0.0)
    normalized.setdefault("method", "offline_public_export")
    normalized["source_row"] = row_number
    return normalized

def ingest_text(
    text: str,
    input_format: str,
    source: SourceDescriptor,
    policy: PublicEvidencePolicy | None = None,
) -> IngestResult:
    policy = policy or PublicEvidencePolicy()
    encoded = text.encode("utf-8")
    if len(encoded) > policy.maximum_input_bytes:
        raise ValueError("Input exceeds policy maximum_input_bytes.")
    licence = evaluate_licence(source)
    if policy.require_licence and not licence.allowed:
        raise PermissionError(licence.reason)
    if source.source_kind not in policy.allowed_source_kinds:
        raise PermissionError("Source kind is not allowed by policy.")
    if source.sensitivity not in policy.allowed_sensitivities:
        raise PermissionError("Source sensitivity is not allowed by policy.")

    records = _parse_text(text, input_format)
    if len(records) > policy.maximum_rows:
        raise ValueError("Input exceeds policy maximum_rows.")

    observations: list[Observation] = []
    quarantined: list[QuarantineRecord] = []
    seen: set[str] = set()
    duplicates = 0
    for row_number, raw in enumerate(records, start=1):
        normalized = _normalize(raw, source, row_number)
        errors = validate_record(normalized, policy)
        if errors:
            quarantined.append(quarantine(row_number, errors, normalized))
            continue
        observation = Observation(
            observation_id=sha256({"source": source.source_id, "row": row_number, "record": normalized})[:24],
            source_id=source.source_id,
            variable=str(normalized["variable"]),
            value=float(normalized["value"]),
            unit=str(normalized["unit"]),
            observed_at=str(normalized["observed_at"]),
            region_id=str(normalized["region_id"]),
            quality_flag=str(normalized["quality_flag"]),
            uncertainty=float(normalized.get("uncertainty", 0.0)),
            method=str(normalized.get("method", "offline_public_export")),
            source_row=row_number,
            sensitivity=str(normalized.get("sensitivity", source.sensitivity)),
            metadata={k: v for k, v in normalized.items() if k not in {
                "source_id", "variable", "value", "unit", "observed_at", "region_id",
                "quality_flag", "uncertainty", "method", "source_row", "sensitivity"
            }},
        )
        semantic_key = sha256({
            "source": observation.source_id,
            "variable": observation.variable,
            "time": observation.observed_at,
            "region": observation.region_id,
            "value": observation.value,
            "unit": observation.unit,
        })
        if semantic_key in seen:
            duplicates += 1
            continue
        seen.add(semantic_key)
        observations.append(observation)

    receipt_payload = {
        "source": source.source_id,
        "format": input_format,
        "input_sha256": sha256(encoded),
        "accepted": len(observations),
        "quarantined": len(quarantined),
        "duplicates": duplicates,
        "observation_root": merkle_root(obs.evidence_hash for obs in observations),
        "quarantine_root": merkle_root(item.record_hash for item in quarantined),
        "policy_hash": policy.policy_hash,
    }
    receipt = IngestReceipt(
        receipt_id=sha256(receipt_payload)[:24],
        source_id=source.source_id,
        input_format=input_format,
        input_sha256=receipt_payload["input_sha256"],
        accepted_count=len(observations),
        quarantined_count=len(quarantined),
        duplicate_count=duplicates,
        observation_merkle_root=receipt_payload["observation_root"],
        quarantine_merkle_root=receipt_payload["quarantine_root"],
        policy_hash=policy.policy_hash,
        deterministic=True,
        claims={
            "network_fetch_performed": False,
            "operational_data_claimed": False,
            "licence_review_performed": True,
            "prohibited_fields_screened": True,
        },
    )
    return IngestResult(tuple(observations), tuple(quarantined), receipt)
