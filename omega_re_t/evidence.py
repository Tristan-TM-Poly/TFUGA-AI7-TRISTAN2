"""Append-only, SHA-256 chained evidence ledger."""

from __future__ import annotations

from dataclasses import dataclass
from json import dumps, loads
from pathlib import Path
from typing import Any, Iterable, Mapping

from .models import ClaimStatus, EvidenceRecord

GENESIS_HASH = "0" * 64


@dataclass(slots=True)
class EvidenceLedger:
    records: list[EvidenceRecord]

    @classmethod
    def empty(cls) -> "EvidenceLedger":
        return cls(records=[])

    @property
    def root_hash(self) -> str:
        return self.records[-1].record_hash if self.records else GENESIS_HASH

    def append(
        self,
        *,
        record_id: str,
        kind: str,
        payload: Mapping[str, Any],
        claim_status: ClaimStatus,
        provenance: Iterable[str] = (),
    ) -> EvidenceRecord:
        if any(record.record_id == record_id for record in self.records):
            raise ValueError(f"Duplicate record_id: {record_id}")
        provenance_tuple = tuple(provenance)
        previous_hash = self.root_hash
        record_hash = EvidenceRecord.compute_hash(
            record_id=record_id,
            kind=kind,
            payload=payload,
            claim_status=claim_status,
            provenance=provenance_tuple,
            previous_hash=previous_hash,
        )
        record = EvidenceRecord(
            record_id=record_id,
            kind=kind,
            payload=dict(payload),
            claim_status=claim_status,
            provenance=provenance_tuple,
            previous_hash=previous_hash,
            record_hash=record_hash,
        )
        self.records.append(record)
        return record

    def verify(self) -> tuple[bool, tuple[str, ...]]:
        errors: list[str] = []
        known_ids: set[str] = set()
        previous = GENESIS_HASH
        for index, record in enumerate(self.records):
            if record.record_id in known_ids:
                errors.append(f"record[{index}] duplicates id {record.record_id}")
            missing = [source for source in record.provenance if source not in known_ids]
            if missing:
                errors.append(f"record[{index}] missing provenance {missing}")
            known_ids.add(record.record_id)
            if record.previous_hash != previous:
                errors.append(f"record[{index}] previous_hash mismatch")
            expected = EvidenceRecord.compute_hash(
                record_id=record.record_id,
                kind=record.kind,
                payload=record.payload,
                claim_status=record.claim_status,
                provenance=record.provenance,
                previous_hash=record.previous_hash,
            )
            if expected != record.record_hash:
                errors.append(f"record[{index}] record_hash mismatch")
            previous = record.record_hash
        return not errors, tuple(errors)

    def to_jsonl(self) -> str:
        return "\n".join(dumps(record.as_dict(), sort_keys=True, ensure_ascii=False) for record in self.records)

    def write(self, path: str | Path) -> None:
        Path(path).write_text(self.to_jsonl() + ("\n" if self.records else ""), encoding="utf-8")

    @classmethod
    def from_jsonl(cls, text: str) -> "EvidenceLedger":
        records: list[EvidenceRecord] = []
        for line in text.splitlines():
            if not line.strip():
                continue
            payload = loads(line)
            records.append(
                EvidenceRecord(
                    record_id=payload["record_id"],
                    kind=payload["kind"],
                    payload=payload["payload"],
                    claim_status=ClaimStatus(payload["claim_status"]),
                    provenance=tuple(payload["provenance"]),
                    previous_hash=payload["previous_hash"],
                    record_hash=payload["record_hash"],
                )
            )
        return cls(records=records)
