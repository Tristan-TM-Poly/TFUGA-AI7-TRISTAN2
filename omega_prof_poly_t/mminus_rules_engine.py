"""Active M-minus rules engine for Omega absorb v1.8."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class MMinusDecision:
    decision: str
    rule: str
    next_action: str


def apply_mminus_rules(context: Mapping[str, object]) -> MMinusDecision:
    if bool(context.get("long_pr_body")):
        return MMinusDecision("shorten_pr_body", "long PR bodies may trigger connector friction", "use_short_pr_template")
    if bool(context.get("strict_version_test")):
        return MMinusDecision("relax_version_assertion", "version tests should be forward compatible", "assert_version_prefix")
    if bool(context.get("restricted_fields")):
        return MMinusDecision("block_record", "restricted fields stop absorption", "stop_before_absorption")
    if bool(context.get("unknown_source")):
        return MMinusDecision("warn_not_crash", "unknown source should warn instead of crash", "route_to_generic_adapter")
    if bool(context.get("claim_without_method")):
        return MMinusDecision("mark_exploratory", "claim without method remains exploratory", "ask_for_method_or_test_seed")
    return MMinusDecision("continue", "no active M-minus rule matched", "continue_pipeline")


def render_mminus_decision(decision: MMinusDecision) -> str:
    return (
        "# M-minus Decision\n\n"
        f"- decision: {decision.decision}\n"
        f"- rule: {decision.rule}\n"
        f"- next action: {decision.next_action}\n"
    )
