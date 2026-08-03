"""Append-only proof ledger with hash-chain verification and revalidation policy."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Iterable

from .models import Authority, stable_id, utc_now
from .scoring import decayed_confidence


GENESIS = "0" * 64


@dataclass(slots=True)
class LedgerEntry:
    id: str
    synergy_id: str
    event: str
    claim: str
    metrics: dict[str, float]
    evidence_hashes: list[str]
    limitations: list[str]
    authority: str
    observed_at: str
    previous_hash: str
    entry_hash: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "synergy_id": self.synergy_id,
            "event": self.event,
            "claim": self.claim,
            "metrics": self.metrics,
            "evidence_hashes": self.evidence_hashes,
            "limitations": self.limitations,
            "authority": self.authority,
            "observed_at": self.observed_at,
            "previous_hash": self.previous_hash,
            "entry_hash": self.entry_hash,
        }


def _hash_payload(payload: dict) -> str:
    material = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


class ProofLedger:
    def __init__(self, path: Path) -> None:
        self.path = path

    def read(self) -> list[LedgerEntry]:
        if not self.path.exists():
            return []
        entries: list[LedgerEntry] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                entries.append(LedgerEntry(**json.loads(line)))
        return entries

    def append(
        self,
        synergy_id: str,
        event: str,
        claim: str,
        metrics: dict[str, float] | None = None,
        evidence_hashes: Iterable[str] = (),
        limitations: Iterable[str] = (),
        authority: Authority = Authority.REVIEW_ONLY,
    ) -> LedgerEntry:
        entries = self.read()
        previous_hash = entries[-1].entry_hash if entries else GENESIS
        observed_at = utc_now()
        base = {
            "id": stable_id("LED", synergy_id, event, observed_at, previous_hash),
            "synergy_id": synergy_id,
            "event": event,
            "claim": claim,
            "metrics": metrics or {},
            "evidence_hashes": sorted(set(evidence_hashes)),
            "limitations": list(limitations),
            "authority": authority.value,
            "observed_at": observed_at,
            "previous_hash": previous_hash,
        }
        entry = LedgerEntry(**base, entry_hash=_hash_payload(base))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry.to_dict(), sort_keys=True, ensure_ascii=False) + "\n")
        return entry

    def verify(self) -> tuple[bool, list[str]]:
        entries = self.read()
        previous = GENESIS
        errors: list[str] = []
        for index, entry in enumerate(entries):
            payload = entry.to_dict()
            expected_hash = payload.pop("entry_hash")
            if entry.previous_hash != previous:
                errors.append(f"entry[{index}]:previous_hash_mismatch")
            actual_hash = _hash_payload(payload)
            if expected_hash != actual_hash:
                errors.append(f"entry[{index}]:entry_hash_mismatch")
            previous = expected_hash
        return not errors, errors


def revalidation_status(last_validated_at: str, initial_confidence: float, half_life_days: float, now: datetime | None = None) -> dict:
    now = now or datetime.now(UTC)
    observed = datetime.fromisoformat(last_validated_at.replace("Z", "+00:00"))
    elapsed_days = max(0.0, (now - observed).total_seconds() / 86400.0)
    confidence = decayed_confidence(initial_confidence, elapsed_days, half_life_days)
    return {
        "last_validated_at": last_validated_at,
        "elapsed_days": round(elapsed_days, 3),
        "half_life_days": half_life_days,
        "decayed_confidence": round(confidence, 6),
        "revalidation_required": confidence < 0.5 * initial_confidence or elapsed_days >= half_life_days,
    }
