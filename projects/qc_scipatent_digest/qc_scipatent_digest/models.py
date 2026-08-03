from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class DigestDocument:
    doc_id: str
    kind: str
    title: str
    year: int
    institution: str
    people: list[str]
    topics: list[str]
    source: str = "synthetic_fixture"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Opportunity:
    opportunity_id: str
    title: str
    science_doc: str
    ip_doc: str
    bridge_topics: list[str]
    oak_status: str
    release_class: str
    cautions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
