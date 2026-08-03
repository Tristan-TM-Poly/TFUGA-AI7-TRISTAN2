from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Literal

DocType = Literal["publication", "patent", "dataset", "report", "unknown"]


@dataclass(slots=True)
class DigestDocument:
    id: str
    type: DocType
    title: str
    year: int | None = None
    source: str = "fixture"
    abstract: str = ""
    authors_or_inventors: list[str] = field(default_factory=list)
    institutions: list[str] = field(default_factory=list)
    owners_or_assignees: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    claims: list[str] = field(default_factory=list)
    url: str | None = None

    def text(self) -> str:
        return " ".join([self.title, self.abstract, " ".join(self.topics), " ".join(self.claims)]).strip()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CVCDDigest:
    document_id: str
    problem: str
    method: str
    object: str
    result: str
    evidence: str
    limits: list[str]
    invariants: list[str]
    residue: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class OAKScore:
    document_id: str
    novelty: float
    evidence: float
    reproducibility: float
    ip_risk: float
    feasibility: float
    tristan_synergy: float
    warnings: list[str] = field(default_factory=list)

    @property
    def total(self) -> float:
        raw = self.novelty + self.evidence + self.reproducibility + self.feasibility + self.tristan_synergy - self.ip_risk
        return round(max(0.0, min(1.0, raw / 5.0)), 3)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["total"] = self.total
        return d


@dataclass(slots=True)
class Opportunity:
    id: str
    name: str
    domain: str
    score: float
    source_documents: list[str]
    prototype: str
    oak_next_test: str
    ip_strategy: str
    risks: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
