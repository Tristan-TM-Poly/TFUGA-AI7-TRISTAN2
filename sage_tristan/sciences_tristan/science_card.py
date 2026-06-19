"""Executable core objects for Ω-ST — Sciences de Tristan.

This module intentionally uses only the Python standard library so the first
Bayes-Tristan / OAK layer can run in minimal environments.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping


class OAKStatus(str, Enum):
    """Ordered OAK maturity statuses.

    Omega_0: intuition
    Omega_1: definition
    Omega_2: formulation
    Omega_3: prototype
    Omega_4: data test
    Omega_5: reproduction
    Omega_6: proof / robust law
    Omega_7: usable technology
    Omega_8: confirmed canon
    """

    OMEGA_0 = "Omega_0"
    OMEGA_1 = "Omega_1"
    OMEGA_2 = "Omega_2"
    OMEGA_3 = "Omega_3"
    OMEGA_4 = "Omega_4"
    OMEGA_5 = "Omega_5"
    OMEGA_6 = "Omega_6"
    OMEGA_7 = "Omega_7"
    OMEGA_8 = "Omega_8"

    @property
    def rank(self) -> int:
        return int(self.value.split("_")[1])

    def can_promote_to(self, target: "OAKStatus") -> bool:
        return target.rank >= self.rank


@dataclass(frozen=True)
class BayesTristanVector:
    """Tensor-like scoring vector for a hypothesis or prototype.

    Scores are normalized in [0, 1]. The vector deliberately separates
    truth from fertility so speculative-but-useful ideas are not promoted as
    proven facts.
    """

    true: float = 0.5
    useful: float = 0.5
    fertile: float = 0.5
    testable: float = 0.5
    safe: float = 0.5
    compressible: float = 0.5
    novel: float = 0.5
    valuable: float = 0.5

    def __post_init__(self) -> None:
        for name, value in self.as_dict().items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1], got {value!r}")

    def as_dict(self) -> dict[str, float]:
        return {
            "true": float(self.true),
            "useful": float(self.useful),
            "fertile": float(self.fertile),
            "testable": float(self.testable),
            "safe": float(self.safe),
            "compressible": float(self.compressible),
            "novel": float(self.novel),
            "valuable": float(self.valuable),
        }

    def priority(self) -> float:
        """Default action-priority score.

        Truth matters, but early Tristan science should prioritize safe,
        useful, fertile, testable ideas with clear next actions.
        """

        weights = {
            "true": 0.14,
            "useful": 0.18,
            "fertile": 0.18,
            "testable": 0.18,
            "safe": 0.10,
            "compressible": 0.08,
            "novel": 0.06,
            "valuable": 0.08,
        }
        return sum(self.as_dict()[axis] * weight for axis, weight in weights.items())

    def promotion_pressure(self) -> float:
        """How ready this card is to move toward higher OAK status."""

        return (
            0.30 * self.true
            + 0.20 * self.testable
            + 0.15 * self.safe
            + 0.15 * self.useful
            + 0.10 * self.compressible
            + 0.10 * self.valuable
        )

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> "BayesTristanVector":
        return cls(**{field_name: float(mapping.get(field_name, 0.5)) for field_name in cls.__dataclass_fields__})


@dataclass
class ScienceCard:
    """Canonical Ω-ST card.

    A card can represent an idea, hypothesis, theory, prototype, residue,
    agent, dataset or memory item.
    """

    id: str
    name: str
    kind: str
    branch: str
    statement: str
    status_oak: OAKStatus
    bayes_tristan: BayesTristanVector
    assumptions: list[str] = field(default_factory=list)
    predictions: list[str] = field(default_factory=list)
    baselines: list[str] = field(default_factory=list)
    tests: list[dict[str, Any]] = field(default_factory=list)
    positive_memory: list[str] = field(default_factory=list)
    negative_memory: list[str] = field(default_factory=list)
    residues: list[str] = field(default_factory=list)
    links: list[dict[str, str]] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
            "branch": self.branch,
            "statement": self.statement,
            "status_oak": self.status_oak.value,
            "bayes_tristan": self.bayes_tristan.as_dict(),
            "assumptions": list(self.assumptions),
            "predictions": list(self.predictions),
            "baselines": list(self.baselines),
            "tests": list(self.tests),
            "positive_memory": list(self.positive_memory),
            "negative_memory": list(self.negative_memory),
            "residues": list(self.residues),
            "links": list(self.links),
            "next_actions": list(self.next_actions),
        }

    def priority(self) -> float:
        action_bonus = 0.04 if self.next_actions else -0.05
        test_bonus = min(len(self.tests), 3) * 0.02
        residue_bonus = min(len(self.residues), 3) * 0.01
        return max(0.0, min(1.0, self.bayes_tristan.priority() + action_bonus + test_bonus + residue_bonus))

    def needs_oak_review(self) -> bool:
        return self.status_oak.rank >= 2 and not self.tests

    def safe_statement(self) -> str:
        if self.status_oak.rank < 4:
            return f"Candidate / exploratory: {self.statement}"
        return self.statement

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> "ScienceCard":
        required = ["id", "name", "kind", "branch", "statement", "status_oak", "bayes_tristan"]
        missing = [key for key in required if key not in mapping]
        if missing:
            raise ValueError(f"missing required science card fields: {missing}")
        status = OAKStatus(mapping["status_oak"])
        vector = BayesTristanVector.from_mapping(mapping["bayes_tristan"])
        return cls(
            id=str(mapping["id"]),
            name=str(mapping["name"]),
            kind=str(mapping["kind"]),
            branch=str(mapping["branch"]),
            statement=str(mapping["statement"]),
            status_oak=status,
            bayes_tristan=vector,
            assumptions=list(mapping.get("assumptions", [])),
            predictions=list(mapping.get("predictions", [])),
            baselines=list(mapping.get("baselines", [])),
            tests=list(mapping.get("tests", [])),
            positive_memory=list(mapping.get("positive_memory", [])),
            negative_memory=list(mapping.get("negative_memory", [])),
            residues=list(mapping.get("residues", [])),
            links=list(mapping.get("links", [])),
            next_actions=list(mapping.get("next_actions", [])),
        )


def cards_from_mappings(items: Iterable[Mapping[str, Any]]) -> list[ScienceCard]:
    return [ScienceCard.from_mapping(item) for item in items]
