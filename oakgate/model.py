"""Typed data model for OAKGate claim evaluation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class EpistemicStatus(str, Enum):
    """Evidence ladder used across MythOS, TheoryOS, PrototypeOS, and RealityOS."""

    MYTH = "M0"
    CONCEPT = "C1"
    FORMALIZATION = "F2"
    SIMULATION = "S3"
    PROTOTYPE = "P4"
    EMPIRICAL = "E5"
    REPRODUCED = "R6"
    CERTIFIED = "T7"
    DEPLOYED = "D8"

    @property
    def rank(self) -> int:
        return list(EpistemicStatus).index(self)


class EpistemicLayer(str, Enum):
    MYTHOS = "MythOS"
    THEORY = "TheoryOS"
    PROTOTYPE = "PrototypeOS"
    REALITY = "RealityOS"


class GateDecision(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class Finding:
    code: str
    severity: GateDecision
    message: str
    remediation: str


@dataclass
class Claim:
    claim_id: str
    text: str
    status: EpistemicStatus
    layer: EpistemicLayer
    evidence: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    uncertainty: float = 1.0
    risks: list[str] = field(default_factory=list)
    ip_classification: str | None = None
    public_intent: bool = False
    source_attributions: list[str] = field(default_factory=list)
    provenance_hash: str | None = None

    def __post_init__(self) -> None:
        if not self.claim_id.strip():
            raise ValueError("claim_id must not be empty")
        if not self.text.strip():
            raise ValueError("text must not be empty")
        if not 0.0 <= self.uncertainty <= 1.0:
            raise ValueError("uncertainty must be between 0 and 1")

    @property
    def claimed_confidence(self) -> float:
        """Confidence implied by the supplied uncertainty value."""

        return 1.0 - self.uncertainty

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Claim":
        return cls(
            claim_id=str(raw["claim_id"]),
            text=str(raw["text"]),
            status=EpistemicStatus(raw["status"]),
            layer=EpistemicLayer(raw["layer"]),
            evidence=[str(item) for item in raw.get("evidence", [])],
            artifacts=[str(item) for item in raw.get("artifacts", [])],
            uncertainty=float(raw.get("uncertainty", 1.0)),
            risks=[str(item) for item in raw.get("risks", [])],
            ip_classification=raw.get("ip_classification"),
            public_intent=bool(raw.get("public_intent", False)),
            source_attributions=[str(item) for item in raw.get("source_attributions", [])],
            provenance_hash=(
                str(raw["provenance_hash"])
                if raw.get("provenance_hash") is not None
                else None
            ),
        )

    def to_dict(self, *, include_provenance: bool = True) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["layer"] = self.layer.value
        if not include_provenance:
            data.pop("provenance_hash", None)
        return data


@dataclass(frozen=True)
class SourceLocation:
    path: str
    start_line: int = 1
    end_line: int = 1

    def __post_init__(self) -> None:
        if self.start_line < 1 or self.end_line < self.start_line:
            raise ValueError("invalid source line range")


@dataclass(frozen=True)
class ScannedClaim:
    claim: Claim
    source: SourceLocation


@dataclass(frozen=True)
class GateReport:
    claim_id: str
    decision: GateDecision
    findings: tuple[Finding, ...]
    source: SourceLocation | None = None
    confidence_debt: float = 0.0
    justified_confidence: float = 0.0

    @property
    def passed(self) -> bool:
        return self.decision is GateDecision.PASS

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "claim_id": self.claim_id,
            "decision": self.decision.value,
            "passed": self.passed,
            "confidence_debt": round(self.confidence_debt, 6),
            "justified_confidence": round(self.justified_confidence, 6),
            "findings": [
                {
                    "code": finding.code,
                    "severity": finding.severity.value,
                    "message": finding.message,
                    "remediation": finding.remediation,
                }
                for finding in self.findings
            ],
        }
        if self.source is not None:
            payload["source"] = asdict(self.source)
        return payload
