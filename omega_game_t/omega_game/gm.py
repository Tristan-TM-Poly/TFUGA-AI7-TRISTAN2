"""GameMaster agent for Ω-GAME-T."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .core import Event, RuleKernel, WorldGraph
from .cvcd import QuestCVCD, WorldCompressor
from .memory import MMinusMemory, MPlusMemory
from .oak import OAKGate, OAKReport


@dataclass(slots=True)
class GMProposal:
    """GameMaster proposal before/after OAK validation."""

    quest: dict[str, Any]
    event: Event
    oak_report: OAKReport | None = None


@dataclass(slots=True)
class GameMasterAgent:
    """Observer + Narrator + Balancer + Judge + WorldWeaver + OAKGate."""

    compressor: WorldCompressor = field(default_factory=WorldCompressor)
    quest_cvcd: QuestCVCD = field(default_factory=QuestCVCD)
    oak_gate: OAKGate = field(default_factory=OAKGate)
    m_minus: MMinusMemory = field(default_factory=MMinusMemory)
    m_plus: MPlusMemory = field(default_factory=MPlusMemory)

    def propose(self, world: WorldGraph) -> GMProposal:
        cvcd_state = self.compressor.compress(world)
        quest = self.quest_cvcd.generate(cvcd_state)
        event = Event(
            event_id=f"gm_event_{len(world.memory) + 1}",
            kind="quest",
            description=quest["quest"],
            actors=self._default_actors(world),
            targets=self._default_targets(world),
            payload={
                "quest": quest,
                "fair": True,
                "fun": True,
                "agency": 0.8,
                "metric": "quest_completion_and_player_choice_divergence",
                "expected_signal": "player faces a meaningful tradeoff",
                "risk_flags": [],
            },
        )
        return GMProposal(quest=quest, event=event)

    def validate_and_apply(
        self,
        world: WorldGraph,
        proposal: GMProposal,
        rule_kernel: RuleKernel | None = None,
    ) -> GMProposal:
        report = self.oak_gate.validate(world, proposal.event, rule_kernel)
        proposal.oak_report = report
        if report.accepted:
            world.remember(
                {
                    "type": "accepted_gm_event",
                    "event_id": proposal.event.event_id,
                    "description": proposal.event.description,
                    "quest": proposal.quest,
                    "oak": report.metrics,
                }
            )
            self.m_plus.record("accepted_gm_event", {"event": proposal.event.description})
        else:
            self.m_minus.record(
                "rejected_gm_event",
                {"event": proposal.event.description, "reasons": report.reasons},
            )
        return proposal

    def step(self, world: WorldGraph, rule_kernel: RuleKernel | None = None) -> GMProposal:
        proposal = self.propose(world)
        return self.validate_and_apply(world, proposal, rule_kernel)

    def _default_actors(self, world: WorldGraph) -> list[str]:
        players = [entity.entity_id for entity in world.entities.values() if entity.kind == "player"]
        if players:
            return players[:1]
        return list(world.entities.keys())[:1]

    def _default_targets(self, world: WorldGraph) -> list[str]:
        non_players = [entity.entity_id for entity in world.entities.values() if entity.kind != "player"]
        return non_players[:1]
