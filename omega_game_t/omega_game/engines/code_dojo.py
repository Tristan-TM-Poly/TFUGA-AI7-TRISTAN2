"""CodeDojoEngine for GameEngineOS-T."""

from __future__ import annotations

from dataclasses import dataclass

from ..kernel import Action, ResourceFlow, SimulationResult, WorldState


@dataclass(slots=True)
class CodeDojoEngine:
    name: str = "CodeDojoEngine-T"

    def propose_actions(self, world: WorldState) -> list[Action]:
        return [
            Action(
                name="read_invariants",
                description="Identify intended behavior before changing a module.",
                expected_flow=ResourceFlow(knowledge=0.22, value=0.05),
                risk=0.04,
                tags=["read", "invariants"],
            ),
            Action(
                name="add_tests",
                description="Add focused checks for current behavior.",
                expected_flow=ResourceFlow(knowledge=0.20, value=0.14),
                risk=0.06,
                tags=["tests", "quality"],
            ),
            Action(
                name="small_refactor",
                description="Improve one small unit while preserving behavior.",
                expected_flow=ResourceFlow(knowledge=0.12, value=0.18),
                risk=0.16,
                tags=["refactor", "small_step"],
            ),
            Action(
                name="write_docs",
                description="Document use, limits and next actions.",
                expected_flow=ResourceFlow(knowledge=0.18, value=0.10),
                risk=0.05,
                tags=["docs", "language"],
            ),
        ]

    def simulate(self, world: WorldState, action: Action) -> SimulationResult:
        tests = min(1.0, world.get("tests", 0.35) + (0.20 if action.name == "add_tests" else 0.05))
        readability = min(1.0, world.get("readability", 0.45) + (0.18 if action.name in {"small_refactor", "write_docs"} else 0.06))
        correctness = min(1.0, world.get("correctness", 0.50) + max(0.0, action.expected_flow.knowledge) * 0.30)
        after = world.with_metric("tests", tests).with_metric("readability", readability).with_metric("correctness", correctness)
        score = max(0.0, min(1.0, 0.20 + 0.30 * tests + 0.25 * readability + 0.25 * correctness - 0.10 * action.risk))
        return SimulationResult(
            engine=self.name,
            before=world,
            action=action,
            after=after,
            flow=action.expected_flow,
            score=score,
            oak_status="accepted" if action.risk < 0.30 else "caution",
            m_plus=[f"{action.name}_completed"],
            m_minus=["avoid_large_unreviewed_change"],
            notes=["Training simulation only; no files are modified by this engine."],
        )


def demo_world() -> WorldState:
    return WorldState(
        name="Python module dojo",
        domain="code",
        resources={"knowledge": 0.5, "value": 0.3},
        metrics={"tests": 0.35, "readability": 0.45, "correctness": 0.55},
        constraints=["small_steps", "tests_before_refactor", "review_required"],
    )


__all__ = ["CodeDojoEngine", "demo_world"]
