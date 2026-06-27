"""TextWorld-T: minimal executable Ω-GAME-T engine."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..core import Entity, RuleKernel, WorldGraph
from ..gm import GameMasterAgent, GMProposal


@dataclass(slots=True)
class TextWorldEngine:
    """A small text-first world loop for fast OAK-safe prototyping."""

    world: WorldGraph = field(default_factory=WorldGraph)
    gm: GameMasterAgent = field(default_factory=GameMasterAgent)
    rule_kernel: RuleKernel = field(default_factory=RuleKernel)

    @classmethod
    def demo_world(cls) -> "TextWorldEngine":
        engine = cls()
        engine.world.add_entity(
            Entity(
                entity_id="player_tristan",
                kind="player",
                name="Tristan",
                attributes={"power": 0.8, "style": "explorer-researcher"},
            )
        )
        engine.world.add_entity(
            Entity(
                entity_id="faction_archivists",
                kind="faction",
                name="Les Archivistes",
                attributes={"power": 0.4, "trust": 0.5},
            )
        )
        engine.world.add_entity(
            Entity(
                entity_id="library_fractal",
                kind="location",
                name="Bibliothèque fractale",
                attributes={"mystery": 0.9},
            )
        )
        engine.world.add_relation("player_tristan", "visited", "library_fractal")
        engine.world.add_relation("faction_archivists", "guards", "library_fractal")
        engine.world.add_hyperedge(
            "quest_seed_archives",
            {"player_tristan", "faction_archivists", "library_fractal"},
        )
        return engine

    def tick(self) -> GMProposal:
        return self.gm.step(self.world, self.rule_kernel)

    def render_last_memory(self) -> str:
        entry = self.world.memory[-1] if self.world.memory else None
        if entry is None:
            return "No world memory yet."
        quest = entry.get("quest", {})
        return (
            f"Quest: {quest.get('quest')}\n"
            f"Objective: {quest.get('objective')}\n"
            f"Constraint: {quest.get('constraint')}\n"
            f"Reward: {quest.get('reward')}\n"
            f"Consequence: {quest.get('consequence')}"
        )
