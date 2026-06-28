"""Core data models for Ω-INFO²-T.

The models are intentionally conservative: they separate truth, utility,
fertility, testability, risk, IP sensitivity, provenance, and OAK status.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


def clamp01(value: float) -> float:
    """Clamp a numeric score to [0, 1]."""
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def json_safe(value: Any) -> Any:
    """Convert dataclass/enum payloads into JSON-safe values."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    return value


class OAKStatus(str, Enum):
    RAW = "RAW"
    PARSED = "PARSED"
    COMPRESSED = "COMPRESSED"
    LINKED = "LINKED"
    TESTABLE = "TESTABLE"
    TESTED = "TESTED"
    FALSIFIED = "FALSIFIED"
    ROBUST = "ROBUST"
    CANONICAL = "CANONICAL"
    DANGEROUS = "DANGEROUS"
    IP_SENSITIVE = "IP-SENSITIVE"


class Route(str, Enum):
    REJECT = "REJECT"
    KEEP_RAW = "KEEP_RAW"
    COMPRESS = "COMPRESS"
    TEST = "TEST"
    LINK = "LINK"
    PROTOTYPE = "PROTOTYPE"
    PATENT_HOLD = "PATENT_HOLD"
    PUBLISH = "PUBLISH"
    MONETIZE = "MONETIZE"
    CANONIZE = "CANONIZE"
    FORGET = "FORGET"
    M_MINUS = "M_MINUS"
    ARCHIVE = "ARCHIVE"
    OAK_REVIEW = "OAK_REVIEW"
    CANON_CANDIDATE = "CANON_CANDIDATE"


@dataclass(slots=True)
class RawObject:
    type: str = "unknown"
    location: str | None = None
    sha256: str | None = None
    content_preview: str | None = None


@dataclass(slots=True)
class Claim:
    text: str
    domain: str = "general"
    source_id: str | None = None
    evidence_ids: list[str] = field(default_factory=list)
    counterevidence_ids: list[str] = field(default_factory=list)
    uncertainty: float = 0.5
    oak_status: OAKStatus = OAKStatus.RAW
    next_test: str | None = None

    def __post_init__(self) -> None:
        self.uncertainty = clamp01(self.uncertainty)


@dataclass(slots=True)
class MetaInformation:
    source: str | None = None
    author: str | None = None
    date_created: str | None = None
    date_accessed: str | None = None
    license: str = "unknown"
    version: str = "unknown"
    language: str = "fr"
    domain: str = "general"


@dataclass(slots=True)
class ProvenanceStep:
    operation: str
    tool: str = "unknown"
    tool_version: str = "unknown"
    parameters: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5
    information_loss: float = 0.0
    errors_detected: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.confidence = clamp01(self.confidence)
        self.information_loss = clamp01(self.information_loss)


@dataclass(slots=True)
class Provenance:
    extraction_tool: str = "unknown"
    extraction_version: str = "0.0"
    transformations: list[ProvenanceStep] = field(default_factory=list)

    @property
    def confidence(self) -> float:
        if not self.transformations:
            return 0.0
        return sum(step.confidence for step in self.transformations) / len(self.transformations)


@dataclass(slots=True)
class UncertaintyTensor:
    source_uncertainty: float = 0.5
    measurement_uncertainty: float = 0.5
    model_uncertainty: float = 0.5
    interpretation_uncertainty: float = 0.5
    temporal_uncertainty: float = 0.5
    license_uncertainty: float = 0.5
    action_uncertainty: float = 0.5

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            setattr(self, name, clamp01(getattr(self, name)))

    @property
    def mean(self) -> float:
        values = [getattr(self, name) for name in self.__dataclass_fields__]
        return sum(values) / len(values)


@dataclass(slots=True)
class InfoScores:
    truth: float = 0.0
    utility: float = 0.0
    fertility: float = 0.0
    novelty: float = 0.0
    testability: float = 0.0
    safety: float = 0.5
    risk: float = 0.5
    freshness: float = 0.5
    ip_sensitivity: float = 0.0
    compression_gain: float = 0.0
    source_trust: float = 0.0

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            setattr(self, name, clamp01(getattr(self, name)))

    @property
    def useful_information_score(self) -> float:
        numerator = (
            self.truth
            * self.utility
            * self.fertility
            * max(self.compression_gain, 0.05)
            * max(self.testability, 0.05)
            * max(self.source_trust, 0.05)
        )
        denominator = max(0.05, self.risk + (1.0 - self.freshness) + self.ip_sensitivity)
        return clamp01(numerator / denominator)


@dataclass(slots=True)
class OAKReport:
    status: OAKStatus = OAKStatus.RAW
    checks_passed: list[str] = field(default_factory=list)
    checks_failed: list[str] = field(default_factory=list)
    residue: list[str] = field(default_factory=list)
    next_test: str | None = None

    @property
    def passed(self) -> bool:
        return not self.checks_failed


@dataclass(slots=True)
class InfoAction:
    recommended_route: Route = Route.ARCHIVE
    next_action: str | None = None


@dataclass(slots=True)
class InfoObject:
    id: str = "info2_0001"
    raw_object: RawObject = field(default_factory=RawObject)
    claims: list[Claim] = field(default_factory=list)
    concepts: list[str] = field(default_factory=list)
    equations: list[str] = field(default_factory=list)
    datasets: list[str] = field(default_factory=list)
    code_fragments: list[str] = field(default_factory=list)
    meta: MetaInformation = field(default_factory=MetaInformation)
    provenance: Provenance = field(default_factory=Provenance)
    uncertainty: UncertaintyTensor = field(default_factory=UncertaintyTensor)
    scores: InfoScores = field(default_factory=InfoScores)
    oak: OAKReport = field(default_factory=OAKReport)
    action: InfoAction = field(default_factory=InfoAction)

    def to_dict(self) -> dict[str, Any]:
        return json_safe(asdict(self))

    @classmethod
    def example(cls) -> "InfoObject":
        return cls(
            id="info2_example_0001",
            raw_object=RawObject(type="theory_note", location="memory/canon/omega-info2"),
            claims=[
                Claim(
                    text="Toute information utile doit porter sa provenance, son incertitude et son action.",
                    domain="information_theory",
                    uncertainty=0.25,
                    oak_status=OAKStatus.TESTABLE,
                    next_test="Apply to a paper, a patent, and an experimental measurement.",
                )
            ],
            concepts=["meta-information", "provenance", "OAK", "CVCD", "Bayes-Tristan"],
            meta=MetaInformation(source="Tristan corpus", author="Tristan Tardif-Morency", domain="meta-information"),
            provenance=Provenance(
                extraction_tool="manual_canon_seed",
                extraction_version="0.1",
                transformations=[
                    ProvenanceStep(operation="seed_theory", tool="ChatGPT", confidence=0.70),
                    ProvenanceStep(operation="compress_cvcd", tool="Ω-CVCD-T", confidence=0.65),
                ],
            ),
        )
