from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional


class MasteryAxis(str, Enum):
    """Axes tensoriels de maîtrise dans Ω-LEARN-T."""

    UNDERSTANDING = "understanding"
    RECALL = "recall"
    TRANSFER = "transfer"
    SPEED = "speed"
    GENERALIZATION = "generalization"
    CREATIVITY = "creativity"
    SAFETY = "safety"
    AUTONOMY = "autonomy"


AXES: List[MasteryAxis] = list(MasteryAxis)


@dataclass(frozen=True)
class Evidence:
    """Bayesian evidence for one mastery axis."""

    axis: MasteryAxis
    successes: int = 0
    failures: int = 0
    weight: float = 1.0
    source: str = "manual"
    timestamp: str = ""

    @classmethod
    def from_mapping(cls, item: Mapping[str, Any]) -> "Evidence":
        return cls(
            axis=MasteryAxis(item.get("axis", MasteryAxis.UNDERSTANDING)),
            successes=int(item.get("successes", 0)),
            failures=int(item.get("failures", 0)),
            weight=float(item.get("weight", 1.0)),
            source=str(item.get("source", "manual")),
            timestamp=str(item.get("timestamp", "")),
        )

    def to_dict(self) -> dict:
        data = asdict(self)
        data["axis"] = self.axis.value
        return data


@dataclass
class ErrorRecord:
    """M⁻ record: an error converted into future-proof learning signal."""

    name: str
    cause: str
    correction: str
    future_test: str
    context: str = ""
    severity: float = 1.0
    status_oak: str = "to_retest"
    timestamp: str = ""

    @classmethod
    def from_mapping(cls, item: Mapping[str, Any]) -> "ErrorRecord":
        return cls(
            name=str(item.get("name", "unnamed error")),
            cause=str(item.get("cause", "unknown")),
            correction=str(item.get("correction", "define correction")),
            future_test=str(item.get("future_test", "create a future test")),
            context=str(item.get("context", "")),
            severity=float(item.get("severity", 1.0)),
            status_oak=str(item.get("status_oak", "to_retest")),
            timestamp=str(item.get("timestamp", "")),
        )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SkillSpec:
    """Input specification for one learning target."""

    skill: str
    goal: str
    notes: str = ""
    evidence: List[Evidence] = field(default_factory=list)
    errors: List[ErrorRecord] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "SkillSpec":
        evidence = [Evidence.from_mapping(x) for x in payload.get("evidence", [])]
        errors = [ErrorRecord.from_mapping(x) for x in payload.get("errors", [])]
        tags = [str(x) for x in payload.get("tags", [])]
        return cls(
            skill=str(payload.get("skill", "Unnamed skill")),
            goal=str(payload.get("goal", "Improve mastery")),
            notes=str(payload.get("notes", "")),
            evidence=evidence,
            errors=errors,
            tags=tags,
        )

    def to_dict(self) -> dict:
        return {
            "skill": self.skill,
            "goal": self.goal,
            "notes": self.notes,
            "evidence": [e.to_dict() for e in self.evidence],
            "errors": [e.to_dict() for e in self.errors],
            "tags": self.tags,
        }


@dataclass
class LearningProfile:
    """Compact state for the learner and skill."""

    spec: SkillSpec
    mastery: Dict[MasteryAxis, float]
    invariants: List[str]
    residues: List[str]
    next_actions: List[str]
    oak_status: str
    negentropy_index: float


@dataclass
class LearningEvent:
    """Persistable event in the Ω-LEARN-T log."""

    event_type: str
    skill: str
    payload: Dict[str, Any]
    timestamp: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "LearningEvent":
        return cls(
            event_type=str(payload.get("event_type", payload.get("type", "event"))),
            skill=str(payload.get("skill", "")),
            payload=dict(payload.get("payload", {})),
            timestamp=str(payload.get("timestamp", "")),
        )


@dataclass
class LearningState:
    """Mutable state that can later be serialized to a database or JSONL log."""

    spec: SkillSpec
    events: List[LearningEvent] = field(default_factory=list)

    def log(self, event_type: str, timestamp: str = "", **payload: Any) -> None:
        self.events.append(
            LearningEvent(event_type=event_type, skill=self.spec.skill, payload=payload, timestamp=timestamp)
        )


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def normalize_axis_scores(raw: Optional[Mapping[MasteryAxis, float]] = None) -> Dict[MasteryAxis, float]:
    raw = raw or {}
    return {axis: clamp01(float(raw.get(axis, 0.5))) for axis in AXES}


def axis_label(axis: MasteryAxis | str) -> str:
    value = axis.value if isinstance(axis, MasteryAxis) else str(axis)
    return value.replace("_", " ")


def mean(values: Iterable[float], default: float = 0.0) -> float:
    vals = list(values)
    return sum(vals) / len(vals) if vals else default
