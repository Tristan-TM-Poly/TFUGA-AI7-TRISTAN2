"""Negative-memory registry and counterexample-preserving failure compression."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping, Sequence

from .catalog import build_antipattern_catalog
from .models import AntiPatternSpec, CellAddress, EvidenceLevel


@dataclass(frozen=True)
class FailureObservation:
    observation_id: str
    antipattern_id: str
    candidate_id: str
    address: CellAddress
    minimal_input: tuple[str, ...]
    expected: str
    observed: str
    reproduction: str
    provenance: str
    severity: int
    resolved: bool = False
    resolution: str = ""

    def __post_init__(self) -> None:
        if not 1 <= self.severity <= 5:
            raise ValueError("severity must lie in [1, 5]")
        if not self.minimal_input:
            raise ValueError("minimal_input must preserve at least one datum")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["address"] = self.address.render()
        return payload

    def digest(self) -> str:
        canonical = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class NegativeMemoryMatch:
    antipattern: AntiPatternSpec
    score: float
    reasons: tuple[str, ...]


@dataclass
class NegativeMemoryRegistry:
    catalog: tuple[AntiPatternSpec, ...] = field(default_factory=build_antipattern_catalog)
    observations: dict[str, FailureObservation] = field(default_factory=dict)

    def __post_init__(self) -> None:
        ids = [item.antipattern_id for item in self.catalog]
        if len(ids) != len(set(ids)):
            raise ValueError("anti-pattern catalog IDs must be unique")
        self._catalog_by_id = {item.antipattern_id: item for item in self.catalog}

    def record(self, observation: FailureObservation) -> str:
        if observation.antipattern_id not in self._catalog_by_id:
            raise KeyError(f"unknown antipattern: {observation.antipattern_id}")
        digest = observation.digest()
        existing = self.observations.get(observation.observation_id)
        if existing is not None and existing != observation:
            raise ValueError(f"observation ID collision: {observation.observation_id}")
        self.observations[observation.observation_id] = observation
        return digest

    def resolve(self, observation_id: str, resolution: str) -> FailureObservation:
        if not resolution.strip():
            raise ValueError("resolution text is required")
        current = self.observations[observation_id]
        updated = FailureObservation(
            **{
                **current.to_dict(),
                "address": current.address,
                "resolved": True,
                "resolution": resolution.strip(),
            }
        )
        self.observations[observation_id] = updated
        return updated

    def active(self) -> tuple[FailureObservation, ...]:
        return tuple(item for item in self.observations.values() if not item.resolved)

    def match(
        self,
        *,
        risk_tags: Iterable[str],
        context: str,
        detector_codes: Iterable[str] = (),
        minimum_score: float = 0.25,
    ) -> tuple[NegativeMemoryMatch, ...]:
        risks = {item.lower() for item in risk_tags}
        detectors = {item.lower() for item in detector_codes}
        matches: list[NegativeMemoryMatch] = []
        for item in self.catalog:
            score = 0.0
            reasons: list[str] = []
            slug_tokens = set(item.antipattern_id.lower().replace(".", "_").split("_"))
            name_tokens = set(item.name.lower().replace("/", " ").replace("-", " ").split())
            if item.context == context:
                score += 0.35
                reasons.append("context")
            risk_overlap = risks & (slug_tokens | name_tokens)
            if risk_overlap:
                score += min(0.4, 0.1 * len(risk_overlap))
                reasons.append("risk:" + ",".join(sorted(risk_overlap)))
            if any(code in item.detector.lower() for code in detectors):
                score += 0.25
                reasons.append("detector")
            if score >= minimum_score:
                matches.append(NegativeMemoryMatch(item, min(score, 1.0), tuple(reasons)))
        matches.sort(key=lambda match: (-match.score, -match.antipattern.severity, match.antipattern.index))
        return tuple(matches)

    def promotion_ceiling(self, matches: Sequence[NegativeMemoryMatch]) -> EvidenceLevel:
        ceiling = EvidenceLevel.FORMAL_PROOF
        for match in matches:
            ceiling = min(ceiling, match.antipattern.blocks_promotion_above)
        return ceiling

    def digest(self) -> str:
        payload = {
            "catalog": [item.to_dict() for item in self.catalog],
            "observations": [self.observations[key].to_dict() for key in sorted(self.observations)],
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return sha256(canonical.encode("utf-8")).hexdigest()

    def receipt(self) -> dict[str, Any]:
        active = self.active()
        return {
            "schema": "omega-sequence-forms-mminus/1",
            "catalog_entries": len(self.catalog),
            "observations": len(self.observations),
            "active_observations": len(active),
            "resolved_observations": len(self.observations) - len(active),
            "digest": self.digest(),
            "global_identity_proved": False,
        }


def minimize_counterexample(
    values: Sequence[str],
    still_fails: callable,
) -> tuple[str, ...]:
    """Deterministic delta-debugging over a finite sequence of textual inputs."""

    current = list(values)
    if not current or not still_fails(tuple(current)):
        raise ValueError("initial values must reproduce the failure")
    granularity = 2
    while len(current) >= 2:
        chunk_size = max(1, len(current) // granularity)
        reduced = False
        for start in range(0, len(current), chunk_size):
            candidate = current[:start] + current[start + chunk_size :]
            if candidate and still_fails(tuple(candidate)):
                current = candidate
                granularity = max(2, granularity - 1)
                reduced = True
                break
        if not reduced:
            if granularity >= len(current):
                break
            granularity = min(len(current), granularity * 2)
    return tuple(current)
