"""DemoForge-T for Ω-GAME-T++.

Convert ProductPlan and SprintPlan objects into internal OAK-safe demo plans.
This module creates scripts and checklists only; it does not publish or launch.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from ..productizer import ProductPlan
from .sprint_forge import SprintPlan


@dataclass(slots=True)
class DemoScene:
    scene_id: str
    title: str
    narration: str
    action: str
    evidence: list[str] = field(default_factory=list)
    oak_notes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.scene_id.strip():
            raise ValueError("DemoScene.scene_id must be non-empty.")
        if not self.title.strip():
            raise ValueError("DemoScene.title must be non-empty.")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class DemoPlan:
    title: str
    product_name: str
    target_engine: str
    audience: list[str]
    opening_hook: str
    scenes: list[DemoScene]
    oak_checklist: list[str]
    success_signals: list[str]
    rehearsal_steps: list[str]

    def __post_init__(self) -> None:
        if not self.scenes:
            raise ValueError("DemoPlan.scenes must be non-empty.")
        if not self.oak_checklist:
            raise ValueError("DemoPlan.oak_checklist must be non-empty.")

    def to_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "product_name": self.product_name,
            "target_engine": self.target_engine,
            "audience": list(self.audience),
            "opening_hook": self.opening_hook,
            "scenes": [scene.to_dict() for scene in self.scenes],
            "oak_checklist": list(self.oak_checklist),
            "success_signals": list(self.success_signals),
            "rehearsal_steps": list(self.rehearsal_steps),
        }

    def to_markdown(self) -> str:
        scenes = "\n\n".join(
            f"## Scene {index}: {scene.title}\n\n"
            f"Narration: {scene.narration}\n\n"
            f"Action: {scene.action}\n\n"
            f"Evidence: {', '.join(scene.evidence) if scene.evidence else 'none'}\n\n"
            f"OAK notes: {', '.join(scene.oak_notes) if scene.oak_notes else 'none'}"
            for index, scene in enumerate(self.scenes, start=1)
        )
        checklist = "\n".join(f"- [ ] {item}" for item in self.oak_checklist)
        signals = "\n".join(f"- {item}" for item in self.success_signals)
        rehearsal = "\n".join(f"- [ ] {item}" for item in self.rehearsal_steps)
        return (
            f"# {self.title}\n\n"
            f"Product: `{self.product_name}`\n\n"
            f"Engine: `{self.target_engine}`\n\n"
            f"Audience: {', '.join(self.audience)}\n\n"
            f"Opening hook: {self.opening_hook}\n\n"
            f"{scenes}\n\n"
            f"## OAK checklist\n\n{checklist}\n\n"
            f"## Success signals\n\n{signals}\n\n"
            f"## Rehearsal steps\n\n{rehearsal}\n"
        )


class DemoForge:
    """Generate internal demo plans from product and sprint plans."""

    def forge(self, product_plan: ProductPlan, sprint_plan: SprintPlan) -> DemoPlan:
        scenes = [
            self._intro_scene(product_plan),
            self._core_loop_scene(product_plan),
            self._proof_scene(product_plan, sprint_plan),
            self._memory_scene(product_plan, sprint_plan),
            self._roadmap_scene(product_plan, sprint_plan),
            self._oak_scene(product_plan),
        ]
        return DemoPlan(
            title=f"{product_plan.product_name} Demo",
            product_name=product_plan.product_name,
            target_engine=product_plan.target_engine,
            audience=list(product_plan.audience),
            opening_hook=self._opening_hook(product_plan),
            scenes=scenes,
            oak_checklist=self._oak_checklist(product_plan, sprint_plan),
            success_signals=self._success_signals(product_plan, sprint_plan),
            rehearsal_steps=self._rehearsal_steps(product_plan, sprint_plan),
        )

    def forge_many(self, pairs: list[tuple[ProductPlan, SprintPlan]]) -> list[DemoPlan]:
        return [self.forge(product, sprint) for product, sprint in pairs]

    def _opening_hook(self, product_plan: ProductPlan) -> str:
        first_value = product_plan.value_props[0] if product_plan.value_props else "turn the world into a playable learning loop"
        return f"Show how {product_plan.product_name} helps users {first_value}."

    def _intro_scene(self, product_plan: ProductPlan) -> DemoScene:
        return DemoScene(
            scene_id="scene_intro",
            title="Introduce the product promise",
            narration=f"This demo presents {product_plan.product_name} for {', '.join(product_plan.audience[:3])}.",
            action="Show product name, source theory, target engine and one-line value proposition.",
            evidence=["ProductPlan", "source_theory", "target_engine"],
            oak_notes=["state that this is an internal demo plan"],
        )

    def _core_loop_scene(self, product_plan: ProductPlan) -> DemoScene:
        deliverable = product_plan.deliverables[0] if product_plan.deliverables else "prototype"
        return DemoScene(
            scene_id="scene_core_loop",
            title="Show the playable loop",
            narration="Demonstrate what the user observes, decides, receives as feedback, and improves.",
            action=f"Walk through the core deliverable `{deliverable}` with visible feedback.",
            evidence=[deliverable, "visible_feedback"],
            oak_notes=["keep model limits visible"],
        )

    def _proof_scene(self, product_plan: ProductPlan, sprint_plan: SprintPlan) -> DemoScene:
        return DemoScene(
            scene_id="scene_proof",
            title="Show measurable proof-of-work",
            narration="Make the demo measurable by showing tests, OAKBench, ProductBench or sprint artifacts.",
            action="Show benchmark notes, sprint total points and completed validation items.",
            evidence=["tests", "oakbench_or_validation_notes", f"total_points={sprint_plan.total_points}"],
            oak_notes=["demo evidence is not the same as scientific validation"],
        )

    def _memory_scene(self, product_plan: ProductPlan, sprint_plan: SprintPlan) -> DemoScene:
        positives = sorted({item for task in sprint_plan.tasks for item in task.positive_memory_expected})[:4]
        negatives = sorted({item for task in sprint_plan.tasks for item in task.negative_memory_avoided})[:4]
        return DemoScene(
            scene_id="scene_memory",
            title="Show M+ and M- learning",
            narration="Explain what the product should reinforce and what it should avoid repeating.",
            action="List expected positive memory and avoided negative patterns.",
            evidence=positives + negatives,
            oak_notes=["use M- to reduce repeated weak patterns"],
        )

    def _roadmap_scene(self, product_plan: ProductPlan, sprint_plan: SprintPlan) -> DemoScene:
        top_tasks = [task.title for task in sprint_plan.tasks[:3]]
        return DemoScene(
            scene_id="scene_roadmap",
            title="Show next sprint roadmap",
            narration="Connect the demo to the next concrete implementation steps.",
            action="Show the top prioritized SprintForge tasks.",
            evidence=top_tasks,
            oak_notes=["do not imply unfinished tasks are already complete"],
        )

    def _oak_scene(self, product_plan: ProductPlan) -> DemoScene:
        return DemoScene(
            scene_id="scene_oak",
            title="Close with OAK controls",
            narration="End by making limits, review status and safe next actions explicit.",
            action="Show OAK controls and review status before any external release.",
            evidence=list(product_plan.oak_controls[:5]),
            oak_notes=["no automatic external release", "human review for sensitive steps"],
        )

    def _oak_checklist(self, product_plan: ProductPlan, sprint_plan: SprintPlan) -> list[str]:
        checklist = [
            "demo_is_internal_until_reviewed",
            "limits_and_assumptions_visible",
            "tests_or_validation_notes_referenced",
            "no_external_publication_from_demo_plan",
        ]
        checklist.extend(product_plan.oak_controls[:4])
        checklist.extend(sprint_plan.oak_gates[:4])
        return list(dict.fromkeys(checklist))

    def _success_signals(self, product_plan: ProductPlan, sprint_plan: SprintPlan) -> list[str]:
        return [
            "audience_understands_value_within_one_minute",
            "core_loop_is_visible",
            "at_least_one_measurable_signal_is_shown",
            "roadmap_next_steps_are_clear",
            f"sprint_total_points_visible_{sprint_plan.total_points}",
            f"target_engine_visible_{product_plan.target_engine}",
        ]

    @staticmethod
    def _rehearsal_steps(product_plan: ProductPlan, sprint_plan: SprintPlan) -> list[str]:
        return [
            "open_product_plan",
            "open_sprint_plan",
            "prepare_demo_output_or_mock",
            "walk_through_scenes_in_order",
            "check_oak_checklist",
            "record_feedback_as_m_plus_or_m_minus",
        ]


def default_demo_forge() -> DemoForge:
    return DemoForge()


__all__ = ["DemoForge", "DemoPlan", "DemoScene", "default_demo_forge"]
