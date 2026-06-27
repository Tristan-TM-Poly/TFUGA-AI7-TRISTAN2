"""Run a minimal VersionForge-T demo."""

from __future__ import annotations

import json

from omega_game import (
    FeedbackDecision,
    FeedbackLoopResult,
    FeedbackSignal,
    default_version_forge,
)


def main() -> None:
    feedback = FeedbackLoopResult(
        product_name="CircuitDungeon-T Lesson Pack",
        target_engine="CircuitDungeon-T",
        confidence_score=0.62,
        decision=FeedbackDecision(
            decision="build_targeted_mini_demo",
            confidence_score=0.62,
            rationale="Signals justify a targeted mini-demo.",
            next_version="v0.2-targeted-mini-demo",
        ),
        feedback_signals=[
            FeedbackSignal(
                signal_type="use_case",
                strength="medium",
                source="private_feedback",
                evidence="reviewer described a classroom use case",
                next_action="create targeted mini-demo",
            )
        ],
        m_plus=["concrete_use_case_found"],
        m_minus=["pricing_not_validated"],
        oak_controls=["no_external_action_from_feedback_loop"],
        next_actions=["create_v0_2_notes"],
    )
    plan = default_version_forge().forge(feedback)
    print(json.dumps(plan.to_dict(), indent=2, ensure_ascii=False))
    print("\n--- MARKDOWN PREVIEW ---\n")
    print(plan.to_markdown())


if __name__ == "__main__":
    main()
