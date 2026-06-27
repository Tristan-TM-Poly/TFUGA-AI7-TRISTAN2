"""PrototypeWorldEngine for GameEngineOS-T."""

from __future__ import annotations

from dataclasses import dataclass

from ..kernel import Action, ResourceFlow, SimulationResult, WorldState


@dataclass(slots=True)
class PrototypeWorldEngine:
    name: str = "PrototypeWorldEngine-T"

    def propose_actions(self, world: WorldState) -> list[Action]:
        return [
            Action(
                name="add_tests",
                description="Add or improve tests for the prototype.",
                expected_flow=ResourceFlow(value=0.08, knowledge=0.25),
                risk=0.08,
                tags=["tests", "oak"],
            ),
            Action(
                name="write_demo",
                description="Create a small internal demo path.",
                expected_flow=ResourceFlow(value=0.18, knowledge=0.12),
                risk=0.12,
                tags=["demo", "product"],
            ),
            Action(
                name="reduce_scope",
                description="Reduce scope to a smaller testable prototype.",
                expected_flow=ResourceFlow(value=0.10, knowledge=0.18),
                risk=0.05,
                tags=["scope", "m_minus"],
            ),
        ]

    def simulate(self, world: WorldState, action: Action) -> SimulationResult:
        testability = min(1.0, world.get("testability", 0.40) + max(0.0, action.expected_flow.knowledge) * 0.5)
        clarity = min(1.0, world.get("clarity", 0.40) + max(0.0, action.expected_flow.value) * 0.4)
        after = world.with_metric("testability", testability).with_metric("clarity", clarity)
        score = max(0.0, min(1.0, 0.40 + 0.30 * testability + 0.20 * clarity - 0.10 * action.risk))
        return SimulationResult(
            engine=self.name,
            before=world,
            action=action,
            after=after,
            flow=action.expected_flow,
            score=score,
            oak_status="accepted" if action.risk < 0.35 else "caution",
            m_plus=[f"{action.name}_advanced"],
            m_minus=["prototype_without_test_reduced"] if action.name == "add_tests" else ["scope_tracked"],
            notes=["Internal prototype simulation only."],
        )


def demo_world() -> WorldState:
    return WorldState(
        name="CircuitDungeon prototype",
        domain="prototype",
        resources={"value": 0.3, "knowledge": 0.4},
        metrics={"testability": 0.45, "clarity": 0.50},
        constraints=["oak_safe", "internal_only"],
    )


__all__ = ["PrototypeWorldEngine", "demo_world"]
