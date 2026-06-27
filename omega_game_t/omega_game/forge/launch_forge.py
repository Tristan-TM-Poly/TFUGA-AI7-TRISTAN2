"""LaunchForge-T for Ω-GAME-T++.

Convert ProductPlan and DemoPlan objects into internal launch drafts. This module
prepares draft assets only; it does not publish, send, sell, or launch.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from ..productizer import ProductPlan
from .demo_forge import DemoPlan


@dataclass(slots=True)
class LandingPageDraft:
    headline: str
    subheadline: str
    bullets: list[str]
    call_to_action: str
    disclaimers: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.headline.strip():
            raise ValueError("LandingPageDraft.headline must be non-empty.")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class PitchDraft:
    one_liner: str
    problem: str
    solution: str
    proof_points: list[str]
    next_ask: str

    def __post_init__(self) -> None:
        if not self.one_liner.strip():
            raise ValueError("PitchDraft.one_liner must be non-empty.")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class LaunchDraft:
    title: str
    product_name: str
    target_engine: str
    status: str
    public_release: str
    landing_page: LandingPageDraft
    pitch: PitchDraft
    audience: list[str]
    channels: list[str]
    demo_assets: list[str]
    oak_checklist: list[str]
    blockers: list[str]
    next_review_actions: list[str]

    def __post_init__(self) -> None:
        if self.status != "internal_draft":
            raise ValueError("LaunchDraft.status must remain internal_draft in this MVP.")
        if not self.oak_checklist:
            raise ValueError("LaunchDraft.oak_checklist must be non-empty.")

    def to_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "product_name": self.product_name,
            "target_engine": self.target_engine,
            "status": self.status,
            "public_release": self.public_release,
            "landing_page": self.landing_page.to_dict(),
            "pitch": self.pitch.to_dict(),
            "audience": list(self.audience),
            "channels": list(self.channels),
            "demo_assets": list(self.demo_assets),
            "oak_checklist": list(self.oak_checklist),
            "blockers": list(self.blockers),
            "next_review_actions": list(self.next_review_actions),
        }

    def to_markdown(self) -> str:
        bullets = "\n".join(f"- {item}" for item in self.landing_page.bullets)
        disclaimers = "\n".join(f"- {item}" for item in self.landing_page.disclaimers)
        proof_points = "\n".join(f"- {item}" for item in self.pitch.proof_points)
        checklist = "\n".join(f"- [ ] {item}" for item in self.oak_checklist)
        blockers = "\n".join(f"- {item}" for item in self.blockers)
        next_actions = "\n".join(f"- [ ] {item}" for item in self.next_review_actions)
        return (
            f"# {self.title}\n\n"
            f"Status: `{self.status}`\n\n"
            f"Public release: `{self.public_release}`\n\n"
            f"Product: `{self.product_name}`\n\n"
            f"Engine: `{self.target_engine}`\n\n"
            f"## Landing page draft\n\n"
            f"### {self.landing_page.headline}\n\n"
            f"{self.landing_page.subheadline}\n\n"
            f"{bullets}\n\n"
            f"CTA: `{self.landing_page.call_to_action}`\n\n"
            f"Disclaimers:\n{disclaimers}\n\n"
            f"## Pitch draft\n\n"
            f"One-liner: {self.pitch.one_liner}\n\n"
            f"Problem: {self.pitch.problem}\n\n"
            f"Solution: {self.pitch.solution}\n\n"
            f"Proof points:\n{proof_points}\n\n"
            f"Next ask: {self.pitch.next_ask}\n\n"
            f"## Audience\n\n{', '.join(self.audience)}\n\n"
            f"## Channels\n\n{', '.join(self.channels)}\n\n"
            f"## Demo assets\n\n{', '.join(self.demo_assets)}\n\n"
            f"## OAK checklist\n\n{checklist}\n\n"
            f"## Blockers\n\n{blockers}\n\n"
            f"## Next review actions\n\n{next_actions}\n"
        )


class LaunchForge:
    """Generate internal launch drafts from product and demo plans."""

    def forge(self, product_plan: ProductPlan, demo_plan: DemoPlan) -> LaunchDraft:
        return LaunchDraft(
            title=f"{product_plan.product_name} Launch Draft",
            product_name=product_plan.product_name,
            target_engine=product_plan.target_engine,
            status="internal_draft",
            public_release="blocked_until_review",
            landing_page=self._landing_page(product_plan, demo_plan),
            pitch=self._pitch(product_plan, demo_plan),
            audience=list(product_plan.audience),
            channels=self._channels(product_plan),
            demo_assets=self._demo_assets(product_plan, demo_plan),
            oak_checklist=self._oak_checklist(product_plan, demo_plan),
            blockers=self._blockers(product_plan),
            next_review_actions=self._next_review_actions(product_plan),
        )

    def forge_many(self, pairs: list[tuple[ProductPlan, DemoPlan]]) -> list[LaunchDraft]:
        return [self.forge(product, demo) for product, demo in pairs]

    def _landing_page(self, product_plan: ProductPlan, demo_plan: DemoPlan) -> LandingPageDraft:
        primary_value = product_plan.value_props[0] if product_plan.value_props else "turn a theory into a playable learning product"
        bullets = product_plan.value_props[:4] + ["OAK-safe internal launch draft", "Demo and validation notes included"]
        return LandingPageDraft(
            headline=f"{product_plan.product_name}: {primary_value}",
            subheadline=demo_plan.opening_hook,
            bullets=list(dict.fromkeys(bullets)),
            call_to_action="Request internal review",
            disclaimers=[
                "internal_draft_not_public_release",
                "review_ip_status_before_public_release",
                "educational_demo_not_scientific_validation",
            ],
        )

    def _pitch(self, product_plan: ProductPlan, demo_plan: DemoPlan) -> PitchDraft:
        audience = ", ".join(product_plan.audience[:3]) or "early users"
        one_liner = f"{product_plan.product_name} helps {audience} through {product_plan.target_engine}."
        problem = product_plan.risks[0] if product_plan.risks else "valuable ideas often stay untested and hard to demonstrate"
        solution = product_plan.value_props[0] if product_plan.value_props else demo_plan.opening_hook
        proof_points = demo_plan.success_signals[:5] + product_plan.deliverables[:3]
        return PitchDraft(
            one_liner=one_liner,
            problem=f"Current friction: {problem}.",
            solution=f"Solution: {solution}.",
            proof_points=list(dict.fromkeys(proof_points)),
            next_ask="Review the demo, OAK checklist, and launch blockers before any public step.",
        )

    def _channels(self, product_plan: ProductPlan) -> list[str]:
        channels = ["internal_demo_review", "private_feedback_session"]
        if any("teacher" in audience or "student" in audience for audience in product_plan.audience):
            channels.append("education_partner_review")
        if any("founder" in audience or "incubator" in audience for audience in product_plan.audience):
            channels.append("incubator_review")
        channels.append("github_pr_review")
        return list(dict.fromkeys(channels))

    def _demo_assets(self, product_plan: ProductPlan, demo_plan: DemoPlan) -> list[str]:
        scene_titles = [scene.title for scene in demo_plan.scenes[:4]]
        return list(dict.fromkeys(product_plan.deliverables[:4] + scene_titles + ["demo_markdown", "oak_checklist"]))

    def _oak_checklist(self, product_plan: ProductPlan, demo_plan: DemoPlan) -> list[str]:
        checklist = [
            "public_release_blocked_until_review",
            "ip_status_reviewed_before_public_step",
            "claims_limited_to_demo_scope",
            "no_external_send_or_publish_from_launch_draft",
        ]
        checklist.extend(product_plan.oak_controls[:5])
        checklist.extend(demo_plan.oak_checklist[:5])
        return list(dict.fromkeys(checklist))

    def _blockers(self, product_plan: ProductPlan) -> list[str]:
        blockers = [
            "ip_review_not_completed",
            "public_copy_not_reviewed",
            "pricing_not_validated",
        ]
        blockers.extend(product_plan.risks[:4])
        return list(dict.fromkeys(blockers))

    @staticmethod
    def _next_review_actions(product_plan: ProductPlan) -> list[str]:
        return [
            "review_product_plan",
            "review_demo_plan",
            "check_ip_classification",
            "verify_oak_controls",
            "decide_private_feedback_scope",
            f"select_next_channel_for_{product_plan.target_engine}",
        ]


def default_launch_forge() -> LaunchForge:
    return LaunchForge()


__all__ = ["LandingPageDraft", "LaunchDraft", "LaunchForge", "PitchDraft", "default_launch_forge"]
