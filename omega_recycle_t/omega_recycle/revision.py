from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json


@dataclass(frozen=True, slots=True)
class RecordRevision:
    key: tuple[str, ...]
    before: dict[str, str] | None
    after: dict[str, str] | None


@dataclass(frozen=True, slots=True)
class RevisionReport:
    changed: bool
    structure_changed: bool
    added: tuple[RecordRevision, ...]
    removed: tuple[RecordRevision, ...]
    modified: tuple[RecordRevision, ...]
    previous_structure_hash: str
    current_structure_hash: str
    claim_boundary: str = "revision_detection_only_not_source_truth_or_semantic_equivalence"


def structure_hash(records: tuple[dict[str, str], ...]) -> str:
    fields = sorted({key for record in records for key in record})
    payload = json.dumps(fields, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def compare_record_snapshots(
    previous: tuple[dict[str, str], ...],
    current: tuple[dict[str, str], ...],
    *,
    key_fields: tuple[str, ...],
) -> RevisionReport:
    if not key_fields:
        raise ValueError("key_fields are required")

    def index(records: tuple[dict[str, str], ...]) -> dict[tuple[str, ...], dict[str, str]]:
        result: dict[tuple[str, ...], dict[str, str]] = {}
        for record in records:
            try:
                key = tuple(record[field] for field in key_fields)
            except KeyError as exc:
                raise ValueError(f"missing key field: {exc.args[0]}") from exc
            if key in result:
                raise ValueError(f"duplicate revision key: {key}")
            result[key] = dict(record)
        return result

    old = index(previous)
    new = index(current)
    added = tuple(RecordRevision(key, None, new[key]) for key in sorted(new.keys() - old.keys()))
    removed = tuple(RecordRevision(key, old[key], None) for key in sorted(old.keys() - new.keys()))
    modified = tuple(
        RecordRevision(key, old[key], new[key])
        for key in sorted(old.keys() & new.keys())
        if old[key] != new[key]
    )
    previous_structure_hash = structure_hash(previous)
    current_structure_hash = structure_hash(current)
    structure_changed = previous_structure_hash != current_structure_hash
    return RevisionReport(
        changed=bool(added or removed or modified or structure_changed),
        structure_changed=structure_changed,
        added=added,
        removed=removed,
        modified=modified,
        previous_structure_hash=previous_structure_hash,
        current_structure_hash=current_structure_hash,
    )
