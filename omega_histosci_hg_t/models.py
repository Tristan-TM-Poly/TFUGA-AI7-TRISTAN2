"""Typed domain model for Ω-HISTOSCI-HG-T∞.

The model separates historical assertions, source-backed evidence, interpretive
relations, negative memory, and software-only validation. No object in this
module certifies historical truth by itself.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping


class NodeKind(str, Enum):
    OBSERVATION = "observation"
    PROBLEM = "problem"
    CONCEPT = "concept"
    HYPOTHESIS = "hypothesis"
    MODEL = "model"
    THEORY = "theory"
    LAW = "law"
    EXPERIMENT = "experiment"
    INSTRUMENT = "instrument"
    MATERIAL = "material"
    DATASET = "dataset"
    METHOD = "method"
    INSTITUTION = "institution"
    PERSON = "person"
    COMMUNITY = "community"
    CONTROVERSY = "controversy"
    ERROR = "error"
    APPLICATION = "application"
    IMPACT = "impact"
    OPEN_PROBLEM = "open_problem"
    BRANCH = "branch"
    EVENT = "event"
    SOURCE = "source"
    PLACE = "place"
    LANGUAGE = "language"


class EdgeKind(str, Enum):
    INFLUENCED_BY = "influenced_by"
    ENABLED_BY = "enabled_by"
    MEASURED_WITH = "measured_with"
    FORMALIZED_BY = "formalized_by"
    CONTRADICTED_BY = "contradicted_by"
    CORRECTED_BY = "corrected_by"
    SPLIT_INTO = "split_into"
    MERGED_WITH = "merged_with"
    TRANSLATED_THROUGH = "translated_through"
    INDEPENDENTLY_DISCOVERED = "independently_discovered"
    INSTITUTIONALIZED_BY = "institutionalized_by"
    APPLIED_TO = "applied_to"
    MISUSED_FOR = "misused_for"
    REMAINS_OPEN = "remains_open"
    REFUTED_BY = "refuted_by"
    NOT_REPRODUCED_BY = "not_reproduced_by"
    DISTORTED_BY = "distorted_by"
    SUPPRESSED_OR_FORGOTTEN_BY = "suppressed_or_forgotten_by"
    MISATTRIBUTED_TO = "misattributed_to"
    ENABLED_EXPLOITATION = "enabled_exploitation"
    CAUSED_UNINTENDED_HARM = "caused_unintended_harm"
    ABANDONED_FOR_LACK_OF_INSTRUMENT = "abandoned_for_lack_of_instrument"
    REDISCOVERED_BY = "rediscovered_by"
    FALSE_AS_THEORY = "false_as_theory"
    FERTILE_FOR_METHOD = "fertile_for_method"
    PARENT_BRANCH = "parent_branch"
    PRECURSOR = "precursor"
    OCCURRED_AT = "occurred_at"
    DOCUMENTED_BY = "documented_by"
    EXPRESSED_IN = "expressed_in"


class EpistemicStatus(str, Enum):
    ESTABLISHED = "established"
    PROBABLE = "probable"
    CONTESTED = "contested"
    UNCERTAIN = "uncertain"
    LEGENDARY = "legendary"
    ANACHRONISTIC = "anachronistic"
    METAPHORICAL = "metaphorical"
    FALSE = "false"
    SOURCE_REPORTED = "source_reported"
    SOFTWARE_FIXTURE = "software_fixture"


class TemporalLayer(str, Enum):
    EMBODIED_PREHISTORY = "layer_0_embodied_prehistory"
    ANCIENT_CIVILIZATIONS = "layer_1_ancient_civilizations"
    MEDIEVAL_GLOBAL_NETWORKS = "layer_2_medieval_global_networks"
    EXPERIMENTAL_MATHEMATIZED = "layer_3_experimental_mathematized"
    INDUSTRIALIZED_SCIENCE = "layer_4_industrialized_science"
    TWENTIETH_CENTURY = "layer_5_twentieth_century"
    DIGITAL_INSTRUMENTED = "layer_6_digital_instrumented"
    AGENT_ASSISTED = "layer_7_agent_assisted"


@dataclass(frozen=True, slots=True)
class SourceReference:
    source_id: str
    title: str
    source_type: str
    authors: tuple[str, ...] = ()
    year: int | None = None
    locator: str | None = None
    language: str | None = None
    primary_source: bool = False
    license: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_id(self.source_id, "source_id")
        if not self.title.strip():
            raise ValueError("source title cannot be blank")
        if self.year is not None and not (-10000 <= self.year <= 3000):
            raise ValueError("source year is outside the supported audit range")


@dataclass(frozen=True, slots=True)
class HistoricalNode:
    node_id: str
    label: str
    kind: NodeKind
    status: EpistemicStatus = EpistemicStatus.SOURCE_REPORTED
    temporal_layers: tuple[TemporalLayer, ...] = ()
    aliases: tuple[str, ...] = ()
    descriptions: tuple[str, ...] = ()
    places: tuple[str, ...] = ()
    languages: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_id(self.node_id, "node_id")
        if not self.label.strip():
            raise ValueError("node label cannot be blank")
        _require_unique(self.aliases, "aliases")
        _require_unique(self.source_ids, "source_ids")


@dataclass(frozen=True, slots=True)
class HistoricalHyperedge:
    edge_id: str
    kind: EdgeKind
    source_node_ids: tuple[str, ...]
    target_node_ids: tuple[str, ...]
    status: EpistemicStatus = EpistemicStatus.SOURCE_REPORTED
    source_ids: tuple[str, ...] = ()
    rationale: str = ""
    confidence: float | None = None
    valid_from_year: int | None = None
    valid_to_year: int | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_id(self.edge_id, "edge_id")
        if not self.source_node_ids:
            raise ValueError("hyperedge must have at least one source node")
        if not self.target_node_ids:
            raise ValueError("hyperedge must have at least one target node")
        _require_unique(self.source_node_ids, "source_node_ids")
        _require_unique(self.target_node_ids, "target_node_ids")
        _require_unique(self.source_ids, "source_ids")
        if set(self.source_node_ids) & set(self.target_node_ids):
            raise ValueError("a node cannot be both source and target in one directed hyperedge")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if (
            self.valid_from_year is not None
            and self.valid_to_year is not None
            and self.valid_from_year > self.valid_to_year
        ):
            raise ValueError("valid_from_year cannot exceed valid_to_year")


@dataclass(frozen=True, slots=True)
class NegativeMemoryRecord:
    memory_id: str
    claim: str
    plausibility_reason: str
    test_or_challenge: str
    failure: str
    cause: str
    lesson: str
    recurrence_risk: str
    source_ids: tuple[str, ...] = ()
    related_node_ids: tuple[str, ...] = ()
    fertile_for_method: bool = False

    def __post_init__(self) -> None:
        _require_id(self.memory_id, "memory_id")
        for name in (
            "claim",
            "plausibility_reason",
            "test_or_challenge",
            "failure",
            "cause",
            "lesson",
            "recurrence_risk",
        ):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} cannot be blank")


@dataclass(frozen=True, slots=True)
class BranchRecord:
    branch_id: str
    canonical_name: str
    parent_branch_ids: tuple[str, ...]
    origin_problems: tuple[str, ...]
    precursor_node_ids: tuple[str, ...] = ()
    key_concept_node_ids: tuple[str, ...] = ()
    instrument_node_ids: tuple[str, ...] = ()
    method_node_ids: tuple[str, ...] = ()
    split_branch_ids: tuple[str, ...] = ()
    merged_branch_ids: tuple[str, ...] = ()
    negative_memory_ids: tuple[str, ...] = ()
    open_problems: tuple[str, ...] = ()
    established_core: tuple[str, ...] = ()
    active_research: tuple[str, ...] = ()
    speculative_extensions: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_id(self.branch_id, "branch_id")
        if not self.canonical_name.strip():
            raise ValueError("canonical_name cannot be blank")
        if not self.origin_problems:
            raise ValueError("branch must declare at least one origin problem")
        for field_name in (
            "parent_branch_ids",
            "precursor_node_ids",
            "key_concept_node_ids",
            "instrument_node_ids",
            "method_node_ids",
            "split_branch_ids",
            "merged_branch_ids",
            "negative_memory_ids",
            "source_ids",
        ):
            _require_unique(getattr(self, field_name), field_name)
        if self.branch_id in self.parent_branch_ids:
            raise ValueError("branch cannot be its own parent")


@dataclass(frozen=True, slots=True)
class HistoricalEvent:
    event_id: str
    problem_node_ids: tuple[str, ...]
    observation_node_ids: tuple[str, ...]
    method_node_ids: tuple[str, ...]
    actor_node_ids: tuple[str, ...]
    context_node_ids: tuple[str, ...]
    evidence_node_ids: tuple[str, ...]
    uncertainty_notes: tuple[str, ...]
    consequence_node_ids: tuple[str, ...]
    year_start: int | None = None
    year_end: int | None = None
    source_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_id(self.event_id, "event_id")
        if not any((self.problem_node_ids, self.observation_node_ids, self.method_node_ids)):
            raise ValueError("event must contain a problem, observation, or method")
        if self.year_start is not None and self.year_end is not None and self.year_start > self.year_end:
            raise ValueError("event year_start cannot exceed year_end")


@dataclass(frozen=True, slots=True)
class OAKEvidence:
    source_quality: float
    primary_source_proximity: float
    independent_corroboration: float
    reproducibility_or_coherence: float
    unresolved_controversy: float
    source_count: int = 0
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "source_quality",
            "primary_source_proximity",
            "independent_corroboration",
            "reproducibility_or_coherence",
            "unresolved_controversy",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.source_count < 0:
            raise ValueError("source_count cannot be negative")


@dataclass(frozen=True, slots=True)
class OAKAssessment:
    score: float
    status: EpistemicStatus
    reasons: tuple[str, ...]
    software_validation_only: bool = True


def canonical_dict(value: Any) -> Any:
    """Convert typed records into deterministic JSON-compatible data."""
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return canonical_dict(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): canonical_dict(value[key]) for key in sorted(value)}
    if isinstance(value, (tuple, list)):
        return [canonical_dict(item) for item in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(canonical_dict(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def content_hash(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _require_id(value: str, field_name: str) -> None:
    if not value or value.strip() != value or " " in value:
        raise ValueError(f"{field_name} must be a nonblank, whitespace-free identifier")


def _require_unique(values: Iterable[str], field_name: str) -> None:
    values = tuple(values)
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must not contain duplicates")
