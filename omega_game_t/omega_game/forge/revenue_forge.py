"""RevenueForge-T for Ω-GAME-T+++.

Convert ProductPlan and LaunchDraft objects into internal revenue hypotheses.
This module does not sell, send, publish, charge, or create external commitments.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from ..productizer import ProductPlan
from .launch_forge import LaunchDraft
from .product_bench import ProductBenchResult, default_product_bench


@dataclass(slots=True)
class PricingHypothesis:
    tier: str
    amount: float
    currency: str
    billing_model: str
    evidence_needed: list[str]

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("PricingHypothesis.amount must be non-negative.")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class OfferSpec:
    name: str
    product_name: str
    audience: list[str]
    promise: str
    deliverables: list[str]
    pricing: PricingHypothesis
    oak_status: str = "internal_review_required"

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("OfferSpec.name must be non-empty.")

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "product_name": self.product_name,
            "audience": list(self.audience),
            "promise": self.promise,
            "deliverables": list(self.deliverables),
            "pricing": self.pricing.to_dict(),
            "oak_status": self.oak_status,
        }


@dataclass(slots=True)
class ChannelMap:
    private: list[str]
    public_after_review: list[str]
    blocked: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class RevenueSignal:
    signal_type: str
    strength: str
    source: str
    evidence: str
    next_action: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class RevenuePlan:
    product_name: str
    target_engine: str
    status: str
    offers: list[OfferSpec]
    channel_map: ChannelMap
    success_signals: list[RevenueSignal]
    oak_controls: list[str]
    product_bench: ProductBenchResult
    next_actions: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.status != "internal_revenue_hypothesis":
            raise ValueError("RevenuePlan.status must remain internal_revenue_hypothesis.")
        if not self.offers:
            raise ValueError("RevenuePlan.offers must be non-empty.")

    def to_dict(self) -> dict[str, object]:
        return {
            "product_name": self.product_name,
            "target_engine": self.target_engine,
            "status": self.status,
            "offers": [offer.to_dict() for offer in self.offers],
            "channel_map": self.channel_map.to_dict(),
            "success_signals": [signal.to_dict() for signal in self.success_signals],
            "oak_controls": list(self.oak_controls),
            "product_bench": self.product_bench.to_dict(),
            "next_actions": list(self.next_actions),
        }

    def to_markdown(self) -> str:
        offers = "\n".join(
            f"- {offer.name}: {offer.pricing.amount:g} {offer.pricing.currency} ({offer.pricing.billing_model})"
            for offer in self.offers
        )
        private = "\n".join(f"- {channel}" for channel in self.channel_map.private)
        blocked = "\n".join(f"- {channel}" for channel in self.channel_map.blocked)
        signals = "\n".join(f"- {signal.signal_type}/{signal.strength}: {signal.next_action}" for signal in self.success_signals)
        controls = "\n".join(f"- [ ] {control}" for control in self.oak_controls)
        actions = "\n".join(f"- [ ] {action}" for action in self.next_actions)
        return (
            f"# {self.product_name} RevenuePlan\n\n"
            f"Status: `{self.status}`\n\n"
            f"Engine: `{self.target_engine}`\n\n"
            f"ProductBench: `{self.product_bench.score:.3f}` / `{self.product_bench.level}`\n\n"
            f"## Offers\n\n{offers}\n\n"
            f"## Private channels\n\n{private}\n\n"
            f"## Blocked channels\n\n{blocked}\n\n"
            f"## Success signals\n\n{signals}\n\n"
            f"## OAK controls\n\n{controls}\n\n"
            f"## Next actions\n\n{actions}\n"
        )


class RevenueForge:
    """Generate internal revenue hypotheses from ProductPlan and LaunchDraft."""

    def forge(self, product_plan: ProductPlan, launch_draft: LaunchDraft) -> RevenuePlan:
        bench = default_product_bench().evaluate(product_plan, launch_draft)
        return RevenuePlan(
            product_name=product_plan.product_name,
            target_engine=product_plan.target_engine,
            status="internal_revenue_hypothesis",
            offers=self._offers(product_plan),
            channel_map=self._channels(launch_draft),
            success_signals=self._signals(product_plan),
            oak_controls=self._oak_controls(product_plan, launch_draft),
            product_bench=bench,
            next_actions=self._next_actions(product_plan, bench),
        )

    def forge_many(self, pairs: list[tuple[ProductPlan, LaunchDraft]]) -> list[RevenuePlan]:
        return [self.forge(product, launch) for product, launch in pairs]

    def _offers(self, product_plan: ProductPlan) -> list[OfferSpec]:
        deliverables = product_plan.deliverables[:4] or ["internal_demo"]
        promise = product_plan.value_props[0] if product_plan.value_props else "make a playable product demo"
        return [
            OfferSpec(
                name=f"{product_plan.product_name} Basic",
                product_name=product_plan.product_name,
                audience=product_plan.audience[:3],
                promise=promise,
                deliverables=deliverables,
                pricing=PricingHypothesis(
                    tier="low",
                    amount=9,
                    currency="CAD",
                    billing_model="one_time_hypothesis",
                    evidence_needed=["private_feedback", "willingness_to_try", "support_cost_estimate"],
                ),
            ),
            OfferSpec(
                name=f"{product_plan.product_name} Standard",
                product_name=product_plan.product_name,
                audience=product_plan.audience[:3],
                promise=promise,
                deliverables=deliverables + ["oakbench_or_productbench_report"],
                pricing=PricingHypothesis(
                    tier="medium",
                    amount=29,
                    currency="CAD",
                    billing_model="one_time_hypothesis",
                    evidence_needed=["price_question", "pilot_feedback", "comparison_signal"],
                ),
            ),
            OfferSpec(
                name=f"{product_plan.product_name} Workshop",
                product_name=product_plan.product_name,
                audience=product_plan.audience[:3],
                promise=promise,
                deliverables=deliverables + ["guided_session", "feedback_summary"],
                pricing=PricingHypothesis(
                    tier="high",
                    amount=99,
                    currency="CAD",
                    billing_model="session_hypothesis",
                    evidence_needed=["group_interest", "schedule_request", "reviewed_scope"],
                ),
            ),
        ]

    def _channels(self, launch_draft: LaunchDraft) -> ChannelMap:
        private = list(dict.fromkeys(launch_draft.channels + ["private_feedback_session", "trusted_reviewer_demo"]))
        return ChannelMap(
            private=private,
            public_after_review=["landing_page_after_review", "demo_video_after_review", "github_release_after_review"],
            blocked=["mass_outreach", "paid_ads_before_review", "public_claims_without_validation"],
        )

    def _signals(self, product_plan: ProductPlan) -> list[RevenueSignal]:
        return [
            RevenueSignal(
                signal_type="interest",
                strength="weak",
                source="private_feedback",
                evidence="user says the demo is interesting",
                next_action="clarify use case",
            ),
            RevenueSignal(
                signal_type="use_case",
                strength="medium",
                source="private_feedback",
                evidence="reviewer describes where they would use it",
                next_action="create targeted mini-demo",
            ),
            RevenueSignal(
                signal_type="price_question",
                strength="strong",
                source="private_feedback",
                evidence="reviewer asks about cost or licensing",
                next_action="test reviewed pricing hypothesis",
            ),
            RevenueSignal(
                signal_type="pilot_request",
                strength="very_strong",
                source="private_feedback",
                evidence="reviewer asks to test with a group",
                next_action="prepare reviewed pilot scope",
            ),
        ]

    def _oak_controls(self, product_plan: ProductPlan, launch_draft: LaunchDraft) -> list[str]:
        controls = [
            "no_automatic_selling",
            "no_external_message_from_revenue_plan",
            "no_public_claim_before_review",
            "signal_is_not_revenue",
            "revenue_is_not_market_validation",
        ]
        controls.extend(product_plan.oak_controls[:5])
        controls.extend(launch_draft.oak_checklist[:5])
        return list(dict.fromkeys(controls))

    def _next_actions(self, product_plan: ProductPlan, bench: ProductBenchResult) -> list[str]:
        actions = [
            "select_one_private_reviewer",
            "run_internal_demo",
            "record_feedback_as_revenue_signal",
            "update_m_plus_and_m_minus",
        ]
        if bench.score >= 0.80:
            actions.append("prepare_private_pilot_scope")
        else:
            actions.append("improve_clarity_before_private_pilot")
        if "review" in product_plan.ip_classification:
            actions.append("complete_ip_status_review")
        return actions


def default_revenue_forge() -> RevenueForge:
    return RevenueForge()


__all__ = [
    "ChannelMap",
    "OfferSpec",
    "PricingHypothesis",
    "RevenueForge",
    "RevenuePlan",
    "RevenueSignal",
    "default_revenue_forge",
]
