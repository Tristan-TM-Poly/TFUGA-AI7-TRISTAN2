from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable

from .models import WorkPacket


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_+-]+", text.lower()))


@dataclass(frozen=True)
class CapabilityMatch:
    capability_id: str
    canonical_name: str
    score: float
    decision: str
    evidence_weight: float
    authority: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "canonical_name": self.canonical_name,
            "score": self.score,
            "decision": self.decision,
            "evidence_weight": self.evidence_weight,
            "authority": self.authority,
        }


def _capability_fields(record: dict[str, Any]) -> tuple[str, str, list[str], list[str], float, str, bool]:
    capability_id = str(record.get("capability_id") or record.get("id") or "")
    name = str(record.get("canonical_name") or record.get("name") or capability_id)
    aliases = [str(item) for item in record.get("aliases", [])]
    domains = [str(item) for item in record.get("domains", [])]
    evidence_weight = float(record.get("evidence_weight", 0.0))
    authority = str(record.get("default_authority") or record.get("authority") or "UNKNOWN")
    reusable = bool(record.get("reusable", True))
    return capability_id, name, aliases, domains, evidence_weight, authority, reusable


def route_capabilities(
    packet: WorkPacket,
    records: Iterable[dict[str, Any]],
    *,
    reuse_threshold: float = 0.45,
) -> tuple[CapabilityMatch, ...]:
    """Deterministic reuse-first router over exported capability contracts.

    R0.1 uses transparent token overlap; it does not pretend that lexical
    similarity establishes semantic substitutability. High-ranked matches are
    candidates for inspection, not automatic execution authority.
    """
    query = _tokens(" ".join([packet.objective, packet.artifact, *packet.tags]))
    matches: list[CapabilityMatch] = []
    for record in records:
        capability_id, name, aliases, domains, evidence_weight, authority, reusable = _capability_fields(record)
        if not capability_id:
            continue
        haystack = _tokens(" ".join([name, *aliases, *domains]))
        overlap = len(query & haystack) / max(1, len(query | haystack))
        score = min(1.0, overlap * 0.85 + max(0.0, min(1.0, evidence_weight)) * 0.15)
        if reusable and score >= reuse_threshold:
            decision = "REUSE_CANDIDATE"
        elif score > 0:
            decision = "EXTEND_OR_INSPECT"
        else:
            decision = "NO_MATCH_SIGNAL"
        matches.append(CapabilityMatch(capability_id, name, score, decision, evidence_weight, authority))
    matches.sort(key=lambda item: (-item.score, item.capability_id))
    return tuple(matches)
