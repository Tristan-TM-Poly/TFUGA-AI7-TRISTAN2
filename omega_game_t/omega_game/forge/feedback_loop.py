"""FeedbackLoop-T for Ω-GAME-T+++.

Convert private feedback signals into M+/M-, confidence, iteration decisions,
and next-version guidance. This module does not contact users or perform any
external action.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .revenue_forge import RevenuePlan, RevenueSignal


STRENGTH_SCORES = {
    "weak": 0.25,
    "medium": 0.55,
    "strong": 0.75,
    "very_strong": 0.90,
}


@dataclass(slots=True)
class FeedbackSignal:
    signal_type: str
    strength: str
    source: str
    evidence: str
    next_action: str

    def __post_init__(self) -> None:
        if self.strength not in STRENGTH_SCORES:
            raise ValueError(f"Unknown feedback strength: {self.strength}")
        if not self.signal_type.strip():
            raise ValueError("FeedbackSignal.signal_type must be non-empty.")

    @property
    def score(self) -> float:
        return STRENGTH_SCORES[self.strength]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["score"] = self.score
        return payload


@dataclass(slots=True)
class FeedbackDecision:
    decision: str
    confidence_score: float
    rationale: str
    next_version: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class FeedbackLoopResult:
    product_name: str
    target_engine: str
    confidence_score: float
    decision: FeedbackDecision
    feedback_signals: list[FeedbackSignal]
    m_plus: list[str]
    m_minus: list[str]
    oak_controls: list[str]
    next_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "product_name": self.product_name,
            "target_engine": self.target_engine,
            "confidence_score": self.confidence_score,
            "decision": self.decision.to_dict(),
            "feedback_signals": [signal.to_dict() for signal in self.feedback_signals],
            "m_plus": list(self.m_plus),
            "m_minus": list(self.m_minus),
            "oak_controls": list(self.oak_controls),
            "next_actions": list(self.next_actions),
        }

    def to_markdown(self) -> str:
        signals = "\n".join(f"- {signal.signal_type}/{signal.strength}: {signal.next_action}" for signal in self.feedback_signals)
        m_plus = "\n".join(f"- {item}" for item in self.m_plus)
        m_minus = "\n".join(f"- {item}" for item in self.m_minus)
        controls = "\n".join(f"- [ ] {item}" for item in self.oak_controls)
        actions = "\n".join(f"- [ ] {item}" for item in self.next_actions)
        return (
            f"# {self.product_name} FeedbackLoop\n\n"
            f"Engine: `{self.target_engine}`\n\n"
            f"Confidence: `{self.confidence_score:.3f}`\n\n"
            f"Decision: `{self.decision.decision}`\n\n"
            f"Next version: `{self.decision.next_version}`\n\n"
            f"## Signals\n\n{signals}\n\n"
            f"## M+\n\n{m_plus}\n\n"
            f"## M-\n\n{m_minus}\n\n"
            f"## OAK controls\n\n{controls}\n\n"
            f"## Next actions\n\n{actions}\n"
        )


class FeedbackLoop:
    """Transform feedback signals into iteration memory and next decisions."""

    def run(self, revenue_plan: RevenuePlan, feedback_signals: list[FeedbackSignal] | None = None) -> FeedbackLoopResult:
        signals = feedback_signals or self._signals_from_revenue_plan(revenue_plan)
        confidence = self._confidence(signals)
        decision = self._decision(confidence)
        m_plus = self._m_plus(signals)
        m_minus = self._m_minus(signals, revenue_plan)
        return FeedbackLoopResult(
            product_name=revenue_plan.product_name,
            target_engine=revenue_plan.target_engine,
            confidence_score=confidence,
            decision=decision,
            feedback_signals=signals,
            m_plus=m_plus,
            m_minus=m_minus,
            oak_controls=self._oak_controls(revenue_plan),
            next_actions=self._next_actions(decision, m_plus, m_minus),
        )

    def run_many(self, revenue_plans: list[RevenuePlan]) -> list[FeedbackLoopResult]:
        return [self.run(plan) for plan in revenue_plans]

    def _signals_from_revenue_plan(self, revenue_plan: RevenuePlan) -> list[FeedbackSignal]:
        return [
            FeedbackSignal(
                signal_type=signal.signal_type,
                strength=signal.strength,
                source=signal.source,
                evidence=signal.evidence,
                next_action=signal.next_action,
            )
            for signal in revenue_plan.success_signals
        ]

    def _confidence(self, signals: list[FeedbackSignal]) -> float:
        if not signals:
            return 0.0
        strength_average = sum(signal.score for signal in signals) / len(signals)
        diversity_bonus = min(0.10, len({signal.signal_type for signal in signals}) * 0.02)
        return max(0.0, min(1.0, strength_average + diversity_bonus))

    def _decision(self, confidence: float) -> FeedbackDecision:
        if confidence >= 0.75:
            return FeedbackDecision(
                decision="prepare_reviewed_private_pilot",
                confidence_score=confidence,
                rationale="Signals are strong enough to prepare a tightly scoped private pilot after review.",
                next_version="v0.3-reviewed-private-pilot",
            )
        if confidence >= 0.55:
            return FeedbackDecision(
                decision="build_targeted_mini_demo",
                confidence_score=confidence,
                rationale="Signals justify a more targeted mini-demo before any broader step.",
                next_version="v0.2-targeted-mini-demo",
            )
        if confidence >= 0.35:
            return FeedbackDecision(
                decision="improve_pitch_and_clarity",
                confidence_score=confidence,
                rationale="Signals exist but clarity and value proposition need improvement.",
                next_version="v0.1-clarity-pass",
            )
        return FeedbackDecision(
            decision="rework_value_proposition",
            confidence_score=confidence,
            rationale="Signals are too weak; refine audience and promise.",
            next_version="v0.1-rework",
        )

    def _m_plus(self, signals: list[FeedbackSignal]) -> list[str]:
        patterns: list[str] = []
        for signal in signals:
            if signal.score >= 0.55:
                patterns.append(f"{signal.signal_type}_signal_found")
            if signal.signal_type == "price_question" and signal.score >= 0.75:
                patterns.append("pricing_conversation_ready_after_review")
            if signal.signal_type == "pilot_request" and signal.score >= 0.75:
                patterns.append("pilot_interest_found")
            if signal.signal_type == "use_case" and signal.score >= 0.55:
                patterns.append("concrete_use_case_found")
        return list(dict.fromkeys(patterns or ["feedback_collected"]))

    def _m_minus(self, signals: list[FeedbackSignal], revenue_plan: RevenuePlan) -> list[str]:
        patterns: list[str] = []
        if any(signal.score < 0.55 for signal in signals):
            patterns.append("weak_signal_needs_clarification")
        if not any(signal.signal_type == "price_question" for signal in signals):
            patterns.append("pricing_not_validated")
        if not any(signal.signal_type in {"use_case", "pilot_request"} for signal in signals):
            patterns.append("use_case_not_confirmed")
        if revenue_plan.product_bench.metrics.scope_creep > 0.45:
            patterns.append("scope_creep_elevated")
        if revenue_plan.product_bench.metrics.ip_uncertainty >= 0.35:
            patterns.append("ip_review_still_required")
        return list(dict.fromkeys(patterns or ["continue_measuring_feedback"] ))

    def _oak_controls(self, revenue_plan: RevenuePlan) -> list[str]:
        controls = [
            "feedback_is_not_market_proof",
            "interest_is_not_revenue",
            "no_external_action_from_feedback_loop",
            "human_review_before_private_pilot",
        ]
        controls.extend(revenue_plan.oak_controls[:5])
        return list(dict.fromkeys(controls))

    @staticmethod
    def _next_actions(decision: FeedbackDecision, m_plus: list[str], m_minus: list[str]) -> list[str]:
        return [
            f"create_{decision.next_version}_notes",
            "append_m_plus_patterns",
            "append_m_minus_patterns",
            "update_product_bench_after_changes",
            "prepare_next_private_feedback_question",
        ]


def default_feedback_loop() -> FeedbackLoop:
    return FeedbackLoop()


__all__ = ["FeedbackDecision", "FeedbackLoop", "FeedbackLoopResult", "FeedbackSignal", "default_feedback_loop"]
