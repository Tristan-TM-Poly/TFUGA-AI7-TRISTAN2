"""Build-To-Green pipeline for pull requests.

The pipeline composes the GreenBuilder planner with Ω-ACTION-EXT-T manifests.
It is still non-executing: it creates reviewable plans, manifests, and reports that
future GitHub connectors can run only after OAK approval.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .core import ActionDNA, RiskTensor
from .green_builder import GreenPlan, GreenStep, PRGreenState, plan_build_to_green, render_plan_markdown
from .manifest import ActionManifest
from .policy import OAKGate


@dataclass(frozen=True)
class PRGreenPacket:
    """Reviewable packet for a PR build-to-green attempt."""

    state: PRGreenState
    plan: GreenPlan
    manifest: ActionManifest
    report_markdown: str

    @property
    def should_execute_without_review(self) -> bool:
        """True only for low-risk, clean merge plans that OAKGate allows."""
        return self.plan.can_merge_now and self.manifest.dry_run.decision.value == "allow_auto"

    def to_dict(self) -> dict[str, Any]:
        return {
            "pr": {
                "number": self.state.number,
                "title": self.state.title,
                "draft": self.state.draft,
                "mergeable": self.state.mergeable,
                "checks_state": self.state.checks_state,
                "has_conflicts": self.state.has_conflicts,
                "changed_files": list(self.state.changed_files),
                "safety_flags": list(self.state.safety_flags),
                "metadata": dict(self.state.metadata),
            },
            "plan": {
                "decision": self.plan.decision,
                "blockers": [blocker.value for blocker in self.plan.blockers],
                "steps": [
                    {
                        "action": step.action.value,
                        "reason": step.reason,
                        "target": step.target,
                        "requires_human": step.requires_human,
                    }
                    for step in self.plan.steps
                ],
            },
            "manifest": self.manifest.to_dict(),
            "report_markdown": self.report_markdown,
            "should_execute_without_review": self.should_execute_without_review,
        }


def risk_for_plan(plan: GreenPlan) -> RiskTensor:
    """Conservative risk estimate for a build-to-green plan."""
    if plan.decision == "merge_now":
        return RiskTensor(ip=1, reputation=1, irreversibility=1)
    if plan.decision == "auto_enrich":
        return RiskTensor(ip=1, reputation=2, irreversibility=1)
    if plan.decision == "wait":
        return RiskTensor()
    if plan.decision == "manual_required":
        return RiskTensor(ip=2, reputation=2, irreversibility=2)
    return RiskTensor(reputation=1)


def action_for_plan(state: PRGreenState, plan: GreenPlan) -> ActionDNA:
    """Compile a PR plan into an external-action DNA object."""
    action_type = {
        "merge_now": "merge_pull_request_when_clean",
        "auto_enrich": "enrich_pull_request_to_green",
        "wait": "wait_for_checks",
        "manual_required": "write_repair_report",
    }.get(plan.decision, "skip_pull_request")

    reversible = plan.decision in {"auto_enrich", "wait"}
    approved = plan.decision == "merge_now" and state.metadata.get("approved") == "true"

    return ActionDNA(
        name=f"PR #{state.number}: {state.title}",
        system="github",
        action_type=action_type,
        risk=risk_for_plan(plan),
        intent="Move a pull request toward green and merge only when clean.",
        target=state.metadata.get("url") or f"pull/{state.number}",
        reversible=reversible,
        rollback="Revert additive repair commits or revert merge commit" if reversible else "Revert merge commit if needed",
        approved=approved,
        public=True,
        destructive=False,
        touches_humans=False,
        touches_money=False,
        touches_ip=True,
        metadata={
            "pr_number": str(state.number),
            "plan_decision": plan.decision,
            "checks_state": state.checks_state,
            "head_sha": state.metadata.get("head_sha", ""),
            "expected_head_sha_required": "true",
        },
    )


def build_green_packet(state: PRGreenState, *, gate: OAKGate | None = None) -> PRGreenPacket:
    """Create a complete reviewable Build-To-Green packet."""
    plan = plan_build_to_green(state)
    action = action_for_plan(state, plan)
    manifest = ActionManifest.compile(action, gate=gate, tags=["pr_build_to_green", plan.decision])
    report = render_plan_markdown(plan)
    return PRGreenPacket(state=state, plan=plan, manifest=manifest, report_markdown=report)


def build_green_packets(states: Iterable[PRGreenState], *, gate: OAKGate | None = None) -> tuple[PRGreenPacket, ...]:
    """Build packets for many PRs in deterministic order."""
    return tuple(build_green_packet(state, gate=gate) for state in sorted(states, key=lambda item: item.number))


def summarize_packets(packets: Iterable[PRGreenPacket]) -> dict[str, list[int]]:
    """Summarize Build-To-Green decisions by PR number."""
    summary: dict[str, list[int]] = {
        "merge_now": [],
        "auto_enrich": [],
        "wait": [],
        "manual_required": [],
        "skip": [],
    }
    for packet in packets:
        summary.setdefault(packet.plan.decision, []).append(packet.state.number)
    return summary


def render_batch_report(packets: Iterable[PRGreenPacket]) -> str:
    """Render a compact batch report for humans and logs."""
    packet_tuple = tuple(packets)
    summary = summarize_packets(packet_tuple)
    lines = ["# PR Build-To-Green batch report", ""]
    for decision, prs in summary.items():
        prs_text = ", ".join(f"#{number}" for number in prs) or "none"
        lines.append(f"- `{decision}`: {prs_text}")
    lines.append("")
    lines.append("## Details")
    for packet in packet_tuple:
        blockers = ", ".join(blocker.value for blocker in packet.plan.blockers) or "none"
        lines.append(f"- PR #{packet.state.number}: `{packet.plan.decision}`; blockers: `{blockers}`; manifest decision: `{packet.manifest.dry_run.decision.value}`.")
    lines.append("")
    lines.append("OAK rule: construction may be automated; merge remains conditional on clean status and expected head SHA.")
    return "\n".join(lines)
