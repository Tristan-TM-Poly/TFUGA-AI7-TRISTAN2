"""GM-Council-T for Ω-GAME-T++.

A deterministic council of specialized GameMaster agents. Each agent proposes a
world intervention; the council aggregates scores, selects the strongest action,
validates it with OAK, and records M+/M- memory.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Protocol

from .core import Event, RuleKernel, WorldGraph
from .cvcd import WorldCompressor
from .memory import MMinusMemory, MPlusMemory
from .oak import OAKGate, OAKReport


@dataclass(slots=True)
class CouncilScores:
    fun: float = 0.5
    agency: float = 0.5
    coherence: float = 0.5
    learning: float = 0.5
    safety: float = 1.0
    novelty: float = 0.5

    def __post_init__(self) -> None:
        for key, value in asdict(self).items():
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{key} must be in [0, 1], got {value!r}")

    def weighted_total(self) -> float:
        return (
            0.18 * self.fun
            + 0.18 * self.agency
            + 0.18 * self.coherence
            + 0.18 * self.learning
            + 0.18 * self.safety
            + 0.10 * self.novelty
        )


@dataclass(slots=True)
class GMVote:
    agent: str
    action: str
    rationale: str
    scores: CouncilScores
    payload: dict[str, object] = field(default_factory=dict)

    @property
    def total(self) -> float:
        return self.scores.weighted_total()

    def to_dict(self) -> dict[str, object]:
        return {
            "agent": self.agent,
            "action": self.action,
            "rationale": self.rationale,
            "scores": asdict(self.scores),
            "total": self.total,
            "payload": dict(self.payload),
        }


@dataclass(slots=True)
class GMCouncilDecision:
    selected_vote: GMVote
    all_votes: list[GMVote]
    oak_report: OAKReport

    @property
    def accepted(self) -> bool:
        return self.oak_report.accepted

    def to_dict(self) -> dict[str, object]:
        return {
            "accepted": self.accepted,
            "selected_vote": self.selected_vote.to_dict(),
            "all_votes": [vote.to_dict() for vote in self.all_votes],
            "oak_reasons": list(self.oak_report.reasons),
            "oak_metrics": dict(self.oak_report.metrics),
        }


class CouncilAgent(Protocol):
    name: str

    def vote(self, world: WorldGraph) -> GMVote:
        ...


@dataclass(slots=True)
class BaseCouncilAgent:
    name: str
    action: str
    rationale: str
    base_scores: CouncilScores

    def vote(self, world: WorldGraph) -> GMVote:
        snapshot = world.snapshot()
        novelty_bonus = min(0.1, len(snapshot["entity_kinds"]) / 100)
        scores = CouncilScores(
            fun=self.base_scores.fun,
            agency=self.base_scores.agency,
            coherence=self.base_scores.coherence,
            learning=self.base_scores.learning,
            safety=self.base_scores.safety,
            novelty=min(1.0, self.base_scores.novelty + novelty_bonus),
        )
        return GMVote(
            agent=self.name,
            action=self.action,
            rationale=self.rationale,
            scores=scores,
            payload={"snapshot": snapshot},
        )


class GMNarrator(BaseCouncilAgent):
    def __init__(self) -> None:
        super().__init__(
            name="GM-Narrator",
            action="add_consequence_thread",
            rationale="Increase narrative continuity by linking the next event to prior memory.",
            base_scores=CouncilScores(fun=0.78, agency=0.70, coherence=0.84, learning=0.62, safety=1.0, novelty=0.76),
        )


class GMStrategist(BaseCouncilAgent):
    def __init__(self) -> None:
        super().__init__(
            name="GM-Strategist",
            action="add_counterplay_choice",
            rationale="Create a readable tradeoff that rewards planning instead of brute repetition.",
            base_scores=CouncilScores(fun=0.80, agency=0.88, coherence=0.82, learning=0.72, safety=1.0, novelty=0.70),
        )


class GMTeacher(BaseCouncilAgent):
    def __init__(self) -> None:
        super().__init__(
            name="GM-Teacher",
            action="add_feedback_loop",
            rationale="Add explicit feedback so the player learns why the outcome happened.",
            base_scores=CouncilScores(fun=0.72, agency=0.80, coherence=0.90, learning=0.95, safety=1.0, novelty=0.66),
        )


class GMScientist(BaseCouncilAgent):
    def __init__(self) -> None:
        super().__init__(
            name="GM-Scientist",
            action="add_residue_measurement",
            rationale="Expose units, measured residue and the domain of validity for the simulation.",
            base_scores=CouncilScores(fun=0.66, agency=0.76, coherence=0.96, learning=0.94, safety=1.0, novelty=0.64),
        )


class GMEconomist(BaseCouncilAgent):
    def __init__(self) -> None:
        super().__init__(
            name="GM-Economist",
            action="add_resource_tradeoff",
            rationale="Make scarcity and resource costs visible before the next decision.",
            base_scores=CouncilScores(fun=0.74, agency=0.86, coherence=0.86, learning=0.80, safety=1.0, novelty=0.68),
        )


class GMMycelium(BaseCouncilAgent):
    def __init__(self) -> None:
        super().__init__(
            name="GM-Mycelium",
            action="connect_dormant_threads",
            rationale="Connect unused entities, memories and future opportunities into one fertile thread.",
            base_scores=CouncilScores(fun=0.82, agency=0.78, coherence=0.82, learning=0.78, safety=1.0, novelty=0.90),
        )


class GMOAK(BaseCouncilAgent):
    def __init__(self) -> None:
        super().__init__(
            name="GM-OAK",
            action="add_oak_checkpoint",
            rationale="Add a coherence, safety and testability checkpoint before the next world change.",
            base_scores=CouncilScores(fun=0.62, agency=0.74, coherence=0.98, learning=0.86, safety=1.0, novelty=0.60),
        )


@dataclass(slots=True)
class GMMemory:
    m_plus: MPlusMemory
    m_minus: MMinusMemory
    name: str = "GM-Memory"

    def vote(self, world: WorldGraph) -> GMVote:
        minus_count = len(self.m_minus.entries)
        plus_count = len(self.m_plus.entries)
        learning = min(1.0, 0.70 + 0.04 * minus_count)
        novelty = 0.72 if minus_count else 0.60
        return GMVote(
            agent=self.name,
            action="reduce_known_antipatterns",
            rationale="Use M+/M- to avoid repeating weak or confusing patterns.",
            scores=CouncilScores(fun=0.68, agency=0.76, coherence=0.88, learning=learning, safety=1.0, novelty=novelty),
            payload={"m_plus_count": plus_count, "m_minus_count": minus_count, "snapshot": world.snapshot()},
        )


@dataclass(slots=True)
class GMCouncil:
    agents: list[CouncilAgent] = field(default_factory=list)
    oak_gate: OAKGate = field(default_factory=OAKGate)
    compressor: WorldCompressor = field(default_factory=WorldCompressor)
    m_plus: MPlusMemory = field(default_factory=MPlusMemory)
    m_minus: MMinusMemory = field(default_factory=MMinusMemory)

    def __post_init__(self) -> None:
        if not self.agents:
            self.agents = [
                GMNarrator(),
                GMStrategist(),
                GMTeacher(),
                GMScientist(),
                GMEconomist(),
                GMMycelium(),
                GMOAK(),
                GMMemory(self.m_plus, self.m_minus),
            ]

    def deliberate(self, world: WorldGraph, rule_kernel: RuleKernel | None = None) -> GMCouncilDecision:
        votes = [agent.vote(world) for agent in self.agents]
        selected = max(votes, key=lambda vote: vote.total)
        cvcd_state = self.compressor.compress(world)
        event = Event(
            event_id=f"gm_council_{len(world.memory) + 1}",
            kind="gm_council_action",
            description=f"{selected.agent}: {selected.action}",
            actors=[],
            targets=[],
            payload={
                "selected_vote": selected.to_dict(),
                "cvcd_tags": cvcd_state.fertile_tags(),
                "fair": True,
                "fun": selected.scores.fun >= 0.5,
                "agency": selected.scores.agency,
                "metric": "gm_council_weighted_vote_quality",
                "expected_signal": "selected action improves world quality without reducing agency",
                "risk_flags": [],
            },
        )
        report = self.oak_gate.validate(world, event, rule_kernel)
        decision = GMCouncilDecision(selected_vote=selected, all_votes=votes, oak_report=report)
        if report.accepted:
            world.remember({"type": "gm_council_decision", "decision": decision.to_dict()})
            self.m_plus.record("gm_council_accepted", decision.to_dict())
        else:
            self.m_minus.record("gm_council_rejected", decision.to_dict())
        return decision


def default_gm_council() -> GMCouncil:
    return GMCouncil()


__all__ = [
    "BaseCouncilAgent",
    "CouncilScores",
    "GMCouncil",
    "GMCouncilDecision",
    "GMEconomist",
    "GMMemory",
    "GMMycelium",
    "GMNarrator",
    "GMOAK",
    "GMScientist",
    "GMStrategist",
    "GMTeacher",
    "GMVote",
    "default_gm_council",
]
