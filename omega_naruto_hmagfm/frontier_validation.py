"""Streaming validation for Ω-NARUTO frontier corpora."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Iterator


@dataclass(frozen=True)
class ValidationFinding:
    code: str
    severity: str
    message: str
    path: str | None = None
    line_number: int | None = None


@dataclass(frozen=True)
class FrontierValidationReport:
    valid: bool
    manifest_records: int
    observed_records: int
    observed_shards: int
    unique_record_ids: int
    findings: tuple[ValidationFinding, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "omega_naruto_frontier.validation.v1",
            "valid": self.valid,
            "manifest_records": self.manifest_records,
            "observed_records": self.observed_records,
            "observed_shards": self.observed_shards,
            "unique_record_ids": self.unique_record_ids,
            "findings": [
                {
                    "code": item.code,
                    "severity": item.severity,
                    "message": item.message,
                    "path": item.path,
                    "line_number": item.line_number,
                }
                for item in self.findings
            ],
            "non_claim": "Validation checks corpus integrity, not scientific truth.",
        }


def _iter_jsonl(path: Path) -> Iterator[tuple[int, dict[str, object], bytes]]:
    with path.open("rb") as handle:
        for line_number, raw in enumerate(handle, start=1):
            if not raw.strip():
                continue
            payload = json.loads(raw)
            yield line_number, payload, raw


def validate_frontier(output_dir: Path) -> FrontierValidationReport:
    manifest_path = output_dir / "manifest.json"
    findings: list[ValidationFinding] = []
    if not manifest_path.exists():
        return FrontierValidationReport(
            valid=False,
            manifest_records=0,
            observed_records=0,
            observed_shards=0,
            unique_record_ids=0,
            findings=(
                ValidationFinding(
                    "MISSING_MANIFEST",
                    "P0",
                    "manifest.json is required",
                    str(manifest_path),
                ),
            ),
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_records = int(manifest.get("written_records", 0))
    shard_entries = manifest.get("shards", [])
    if not isinstance(shard_entries, list):
        shard_entries = []
        findings.append(
            ValidationFinding("INVALID_SHARD_LIST", "P0", "manifest shards must be a list")
        )

    observed_records = 0
    record_ids: set[str] = set()
    expected_ordinal = int(manifest.get("start_ordinal", 0))
    corpus_digest = sha256()

    for shard in shard_entries:
        path = output_dir / str(shard.get("path", ""))
        if not path.exists():
            findings.append(
                ValidationFinding("MISSING_SHARD", "P0", "declared shard is missing", str(path))
            )
            continue
        encoded = path.read_bytes()
        observed_hash = sha256(encoded).hexdigest()
        expected_hash = str(shard.get("sha256", ""))
        if observed_hash != expected_hash:
            findings.append(
                ValidationFinding(
                    "SHARD_HASH_MISMATCH",
                    "P0",
                    f"expected {expected_hash}, observed {observed_hash}",
                    str(path),
                )
            )
        declared_bytes = int(shard.get("byte_count", -1))
        if declared_bytes != len(encoded):
            findings.append(
                ValidationFinding(
                    "SHARD_BYTE_COUNT_MISMATCH",
                    "P1",
                    f"expected {declared_bytes}, observed {len(encoded)}",
                    str(path),
                )
            )

        local_count = 0
        for line_number, payload, raw in _iter_jsonl(path):
            local_count += 1
            observed_records += 1
            corpus_digest.update(raw)
            ordinal = payload.get("ordinal")
            if ordinal != expected_ordinal:
                findings.append(
                    ValidationFinding(
                        "ORDINAL_GAP",
                        "P0",
                        f"expected ordinal {expected_ordinal}, observed {ordinal}",
                        str(path),
                        line_number,
                    )
                )
                if isinstance(ordinal, int):
                    expected_ordinal = ordinal
            expected_ordinal += 1
            record_id = payload.get("record_id")
            if not isinstance(record_id, str) or not record_id:
                findings.append(
                    ValidationFinding(
                        "MISSING_RECORD_ID",
                        "P0",
                        "record_id must be a non-empty string",
                        str(path),
                        line_number,
                    )
                )
            elif record_id in record_ids:
                findings.append(
                    ValidationFinding(
                        "DUPLICATE_RECORD_ID",
                        "P0",
                        f"duplicate record_id {record_id}",
                        str(path),
                        line_number,
                    )
                )
            else:
                record_ids.add(record_id)
            if "not evidence or physical validation" not in str(payload.get("non_claim", "")):
                findings.append(
                    ValidationFinding(
                        "MISSING_NON_CLAIM",
                        "P1",
                        "record does not preserve the OAK non-claim boundary",
                        str(path),
                        line_number,
                    )
                )

        declared_count = int(shard.get("record_count", -1))
        if declared_count != local_count:
            findings.append(
                ValidationFinding(
                    "SHARD_RECORD_COUNT_MISMATCH",
                    "P0",
                    f"expected {declared_count}, observed {local_count}",
                    str(path),
                )
            )

    if observed_records != manifest_records:
        findings.append(
            ValidationFinding(
                "MANIFEST_RECORD_COUNT_MISMATCH",
                "P0",
                f"expected {manifest_records}, observed {observed_records}",
            )
        )
    if len(record_ids) != observed_records:
        findings.append(
            ValidationFinding(
                "RECORD_ID_CARDINALITY_MISMATCH",
                "P0",
                f"expected {observed_records} unique IDs, observed {len(record_ids)}",
            )
        )

    expected_corpus_hash = str(manifest.get("corpus_sha256", ""))
    observed_corpus_hash = corpus_digest.hexdigest()
    if observed_corpus_hash != expected_corpus_hash:
        findings.append(
            ValidationFinding(
                "CORPUS_HASH_MISMATCH",
                "P0",
                f"expected {expected_corpus_hash}, observed {observed_corpus_hash}",
            )
        )

    valid = not any(item.severity == "P0" for item in findings)
    return FrontierValidationReport(
        valid=valid,
        manifest_records=manifest_records,
        observed_records=observed_records,
        observed_shards=len(shard_entries),
        unique_record_ids=len(record_ids),
        findings=tuple(findings),
    )
