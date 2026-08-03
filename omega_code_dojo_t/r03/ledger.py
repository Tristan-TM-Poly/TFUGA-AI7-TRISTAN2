from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .hashing import sha256_hex
from .models import LearningReport


@dataclass(frozen=True)
class LedgerEntry:
    sequence: int
    previous_hash: str
    payload_hash: str
    entry_hash: str
    report_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "previous_hash": self.previous_hash,
            "payload_hash": self.payload_hash,
            "entry_hash": self.entry_hash,
            "report_id": self.report_id,
        }


@dataclass
class LearningLedger:
    entries: list[LedgerEntry] = field(default_factory=list)

    def append(self, report: LearningReport) -> LedgerEntry:
        previous_hash = self.entries[-1].entry_hash if self.entries else "GENESIS"
        payload_hash = sha256_hex(report.to_dict())
        sequence = len(self.entries)
        entry_hash = sha256_hex(
            {
                "sequence": sequence,
                "previous_hash": previous_hash,
                "payload_hash": payload_hash,
                "report_id": report.report_id,
            }
        )
        entry = LedgerEntry(
            sequence=sequence,
            previous_hash=previous_hash,
            payload_hash=payload_hash,
            entry_hash=entry_hash,
            report_id=report.report_id,
        )
        self.entries.append(entry)
        return entry

    def verify(
        self,
        reports: Mapping[str, LearningReport],
    ) -> bool:
        previous_hash = "GENESIS"
        for expected_sequence, entry in enumerate(self.entries):
            report = reports.get(entry.report_id)
            if report is None:
                return False
            payload_hash = sha256_hex(report.to_dict())
            expected_hash = sha256_hex(
                {
                    "sequence": expected_sequence,
                    "previous_hash": previous_hash,
                    "payload_hash": payload_hash,
                    "report_id": entry.report_id,
                }
            )
            if (
                entry.sequence != expected_sequence
                or entry.previous_hash != previous_hash
                or entry.payload_hash != payload_hash
                or entry.entry_hash != expected_hash
            ):
                return False
            previous_hash = entry.entry_hash
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "count": len(self.entries),
            "entries": [item.to_dict() for item in self.entries],
            "head_hash": self.entries[-1].entry_hash if self.entries else "GENESIS",
        }
