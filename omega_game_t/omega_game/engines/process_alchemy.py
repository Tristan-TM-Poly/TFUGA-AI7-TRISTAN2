"""ProcessAlchemyEngine for GameEngineOS-T.

Safe abstract process simulation only. No real-world protocol is generated.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..kernel import Action, ResourceFlow, SimulationResult, WorldState


@dataclass(slots=True)
class ProcessAlchemyEngine:
    name: str = "ProcessAlchemyEngine-T"

    def propose_actions(self, world: WorldState) -> list[Action]:
        return [
            Action(
                name="generic_transform",
                description="Apply an abstract transformation step to improve useful output.",
                expected_flow=ResourceFlow(energy=-0.12, matter=0.18, knowledge=0.10),
                risk=0.18,
                tags=["abstract_process", "model_only"],
            ),
            Action(
                name="quality_check",
                description="Measure quality and route uncertain output to review.",
                expected_flow=ResourceFlow(matter=0.05, knowledge=0.22),
                risk=0.06,
                tags=["quality", "oak"],
            ),
            Action(
                name="recycle_residue",
                description="Route residual stream into a generic reuse loop.",
                expected_flow=ResourceFlow(energy=-0.05, matter=0.20, value=0.10, knowledge=0.08),
                risk=0.12,
                tags=["recycle", "circularity"],
            ),
        ]

    def simulate(self, world: WorldState, action: Action) -> SimulationResult:
        quality = min(1.0, world.get("quality", 0.45) + max(0.0, action.expected_flow.matter) * 0.35)
        circularity = min(1.0, world.get("circularity", 0.30) + (0.20 if action.name == "recycle_residue" else 0.05))
        safety = max(0.0, min(1.0, world.get("safety", 0.80) - action.risk * 0.10))
        after = world.with_metric("quality", quality).with_metric("circularity", circularity).with_metric("safety", safety)
        score = max(0.0, min(1.0, 0.25 + 0.25 * quality + 0.25 * circularity + 0.25 * safety - 0.10 * action.risk))
        oak_status = "accepted" if action.risk < 0.20 else "caution"
        return SimulationResult(
            engine=self.name,
            before=world,
            action=action,
            after=after,
            flow=action.expected_flow,
            score=score,
            oak_status=oak_status,
            m_plus=[f"{action.name}_improved_model"],
            m_minus=["no_real_world_protocol", "assumptions_visible"],
            notes=["Abstract process model only; no operational procedure."],
        )


def demo_world() -> WorldState:
    return WorldState(
        name="Generic circular process",
        domain="process_model",
        resources={"matter": 0.5, "energy": 0.4, "knowledge": 0.3},
        metrics={"quality": 0.45, "circularity": 0.35, "safety": 0.90},
        constraints=["model_only", "no_protocol", "professional_review_for_real_world_use"],
    )


__all__ = ["ProcessAlchemyEngine", "demo_world"]
