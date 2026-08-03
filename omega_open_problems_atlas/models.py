"""Typed records for Ω-OPEN-PROBLEMS-ATLAS-T∞.

All records are deliberately explicit about provenance and epistemic state.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any


class OpenStatus(str, Enum):
    DISCOVERED_UNVERIFIED = "DISCOVERED_UNVERIFIED"
    SOURCE_REPORTED_OPEN = "SOURCE_REPORTED_OPEN"
    INDEPENDENTLY_CHECKED_OPEN = "INDEPENDENTLY_CHECKED_OPEN"
    PARTIALLY_RESOLVED = "PARTIALLY_RESOLVED"
    RESOLVED = "RESOLVED"
    STATUS_DISPUTED = "STATUS_DISPUTED"
    STALE_SOURCE = "STALE_SOURCE"


class EpistemicStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    SOURCE_VERIFIED = "SOURCE_VERIFIED"
    OPEN_STATUS_CHECKED = "OPEN_STATUS_CHECKED"
    NORMALIZED = "NORMALIZED"
    LITERATURE_BASELINED = "LITERATURE_BASELINED"
    DECOMPOSED = "DECOMPOSED"
    COMPUTATIONALLY_PROBED = "COMPUTATIONALLY_PROBED"
    PARTIAL_PROGRESS = "PARTIAL_PROGRESS"
    INDEPENDENTLY_REPRODUCED = "INDEPENDENTLY_REPRODUCED"
    FORMALIZED_OR_PEER_REVIEWED = "FORMALIZED_OR_PEER_REVIEWED"
    CANON_CANDIDATE = "CANON_CANDIDATE"


class ProblemKind(str, Enum):
    RESEARCH_PROBLEM = "RESEARCH_PROBLEM"
    CONJECTURE = "CONJECTURE"
    CLASSIFICATION = "CLASSIFICATION"
    BOUND_IMPROVEMENT = "BOUND_IMPROVEMENT"
    COUNTEREXAMPLE_SEARCH = "COUNTEREXAMPLE_SEARCH"
    FORMALIZATION_TARGET = "FORMALIZATION_TARGET"
    COMPETITION_PROBLEM = "COMPETITION_PROBLEM"
    COMPUTATIONAL_CHALLENGE = "COMPUTATIONAL_CHALLENGE"
    RESEARCH_CELL = "RESEARCH_CELL"


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    name: str
    canonical_url: str
    source_type: str
    authority_class: str
    redistribution_policy: str
    requires_status_recheck: bool = True
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProblemGenome:
    problem_id: str
    title: str
    statement: str
    source_id: str
    source_locator: str
    kind: ProblemKind
    domains: tuple[str, ...]
    objects: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    quantifiers: tuple[str, ...] = ()
    known_results: tuple[str, ...] = ()
    related_problem_ids: tuple[str, ...] = ()
    reusable_methods: tuple[str, ...] = ()
    open_status: OpenStatus = OpenStatus.DISCOVERED_UNVERIFIED
    epistemic_status: EpistemicStatus = EpistemicStatus.DISCOVERED
    last_status_check: str | None = None
    literature_search_required: bool = True
    human_review_required: bool = True
    finite_computation_is_not_proof: bool = True
    solution_claimed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def normalized_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["kind"] = self.kind.value
        payload["open_status"] = self.open_status.value
        payload["epistemic_status"] = self.epistemic_status.value
        return payload

    def statement_hash(self) -> str:
        normalized = " ".join(self.statement.split())
        return sha256(normalized.encode("utf-8")).hexdigest()

    def record_hash(self) -> str:
        encoded = json.dumps(
            self.normalized_payload(), sort_keys=True, ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        return sha256(encoded).hexdigest()


@dataclass(frozen=True)
class ResearchCell:
    cell_id: str
    domain: str
    research_operator: str
    objective: str
    status: str = "UNMATERIALIZED_RESEARCH_SLOT"
    is_verified_open_problem: bool = False
    solution_claimed: bool = False
    finite_computation_is_not_proof: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
