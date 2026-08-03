from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class OAKStatus(str, Enum):
    SPECULATIVE = "S"
    EXPLORATORY = "E"
    CRYSTALLIZABLE = "X"
    DEMONSTRATED = "D"
    CANONICAL = "C"
    ARCHIVED = "A"


class DisclosureClass(str, Enum):
    OPEN_PUBLIC = "OPEN_PUBLIC"
    PUBLIC_AFTER_REVIEW = "PUBLIC_AFTER_REVIEW"
    PATENT_CANDIDATE = "PATENT_CANDIDATE"
    TRADE_SECRET = "TRADE_SECRET"
    PRIVATE_CLIENT = "PRIVATE_CLIENT"
    RESTRICTED_SAFETY = "RESTRICTED_SAFETY"
    ARCHIVE_ONLY = "ARCHIVE_ONLY"


class RevenuePath(str, Enum):
    SPONSORSHIP = "sponsorship"
    FIXED_SCOPE_SERVICE = "fixed_scope_service"
    RECURRING_SERVICE = "recurring_service"
    SOFTWARE_PRODUCT = "software_product"
    GITHUB_APP = "github_app"
    API = "api"
    LICENSE = "license"
    TRAINING = "training"
    RESEARCH_CONTRACT = "research_contract"


class ExperimentDecision(str, Enum):
    CONTINUE = "continue"
    SCALE = "scale"
    REVISE = "revise"
    STOP = "stop"


@dataclass(frozen=True)
class Evidence:
    tests: int = 0
    reproducible_demo: bool = False
    benchmark: bool = False
    external_reproduction: bool = False
    paying_user: bool = False
    limitations_documented: bool = False

    def validate(self) -> None:
        if self.tests < 0:
            raise ValueError("tests must be non-negative")


@dataclass(frozen=True)
class Artifact:
    artifact_id: str
    title: str
    problem: str
    actor: str
    oak_status: OAKStatus
    disclosure: DisclosureClass
    revenue_paths: tuple[RevenuePath, ...]
    evidence: Evidence = field(default_factory=Evidence)
    utility: float = 0.0
    reuse: float = 0.0
    discoverability: float = 0.0
    trust: float = 0.0
    conversion_clarity: float = 0.0
    noise: float = 0.0
    maintenance_burden: float = 0.0
    ip_legal_risk: float = 0.0
    safety_privacy_risk: float = 0.0
    risks: tuple[str, ...] = ()
    next_action: str = ""

    def validate(self) -> None:
        if not self.artifact_id.strip():
            raise ValueError("artifact_id is required")
        if not self.title.strip():
            raise ValueError("title is required")
        if not self.problem.strip():
            raise ValueError("problem is required")
        if not self.actor.strip():
            raise ValueError("actor is required")
        if not self.revenue_paths:
            raise ValueError("at least one revenue path is required")
        for name in (
            "utility",
            "reuse",
            "discoverability",
            "trust",
            "conversion_clarity",
            "noise",
            "maintenance_burden",
            "ip_legal_risk",
            "safety_privacy_risk",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        self.evidence.validate()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["oak_status"] = self.oak_status.value
        data["disclosure"] = self.disclosure.value
        data["revenue_paths"] = [path.value for path in self.revenue_paths]
        return data


@dataclass(frozen=True)
class Offer:
    offer_id: str
    artifact_id: str
    title: str
    scope: tuple[str, ...]
    deliverables: tuple[str, ...]
    exclusions: tuple[str, ...]
    revenue_path: RevenuePath
    sustainable: bool
    rationale: str


@dataclass(frozen=True)
class SponsorTier:
    name: str
    monthly_minor: int
    currency: str
    monthly_delivery_minutes: int
    benefits: tuple[str, ...]
    unlimited_custom_work: bool = False

    def validate(self) -> None:
        if self.monthly_minor <= 0:
            raise ValueError("monthly_minor must be positive")
        if self.monthly_delivery_minutes < 0:
            raise ValueError("monthly_delivery_minutes must be non-negative")
        if len(self.currency) != 3:
            raise ValueError("currency must be a three-letter code")


@dataclass(frozen=True)
class RevenueEvent:
    event_id: str
    source: str
    gross_minor: int
    currency: str
    fee_minor: int
    occurred_at: str
    category: str = "revenue"

    def validate(self) -> None:
        if not self.event_id.strip():
            raise ValueError("event_id is required")
        if self.gross_minor < 0 or self.fee_minor < 0:
            raise ValueError("money values must be non-negative")
        if self.fee_minor > self.gross_minor:
            raise ValueError("fee_minor cannot exceed gross_minor")
        if len(self.currency) != 3:
            raise ValueError("currency must be a three-letter code")

    @property
    def net_minor(self) -> int:
        return self.gross_minor - self.fee_minor

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self) | {"net_minor": self.net_minor}


@dataclass(frozen=True)
class Experiment:
    experiment_id: str
    hypothesis: str
    target_metric: str
    target_value: float
    observed_value: float
    minimum_sample: int
    observed_sample: int
    hard_failure: bool = False

    def validate(self) -> None:
        if not self.experiment_id.strip():
            raise ValueError("experiment_id is required")
        if self.target_value < 0 or self.observed_value < 0:
            raise ValueError("metric values must be non-negative")
        if self.minimum_sample < 0 or self.observed_sample < 0:
            raise ValueError("sample sizes must be non-negative")
