from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from .core import IPClass, Signal
from .oakbench import OAKBenchResult, run_oakbench

IssueIntent = Literal["repair", "source_repair", "ip_review", "prototype", "commercial_validation", "observe"]


@dataclass(frozen=True)
class GitHubIssueDraft:
    """Public-safe GitHub issue draft generated from an OAKBench result.

    This object deliberately contains only public-safe text. It never calls the
    GitHub API. Connector or workflow code can use it after explicit approval.
    """

    title: str
    body: str
    labels: tuple[str, ...]
    intent: IssueIntent
    public_safe: bool
    blocked_external_actions: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "body": self.body,
            "labels": list(self.labels),
            "intent": self.intent,
            "public_safe": self.public_safe,
            "blocked_external_actions": list(self.blocked_external_actions),
        }


def _slug_words(text: str, *, limit: int = 78) -> str:
    cleaned = re.sub(r"\s+", " ", text.strip())
    return cleaned[:limit].rstrip() or "DeepTech signal"


def _checkbox_lines(items: tuple[str, ...] | list[str]) -> str:
    if not items:
        return "- [ ] None recorded."
    return "\n".join(f"- [ ] {item}" for item in items)


def _bullet_lines(items: tuple[str, ...] | list[str]) -> str:
    if not items:
        return "- None recorded."
    return "\n".join(f"- {item}" for item in items)


def _intent(result: OAKBenchResult) -> IssueIntent:
    if result.priority_band == "blocked":
        return "repair"
    if result.priority_band == "repair":
        return "source_repair"
    if result.priority_band == "review":
        return "ip_review"
    if result.priority_band == "commercialize":
        return "commercial_validation"
    if result.priority_band == "build":
        return "prototype"
    return "observe"


def _labels(result: OAKBenchResult, intent: IssueIntent) -> tuple[str, ...]:
    labels = ["OAK", "deeptech-forge", f"band:{result.priority_band}", f"intent:{intent}"]
    if result.ip_review_required:
        labels.append("ip-review")
    if result.public_action_allowed:
        labels.append("public-safe")
    else:
        labels.append("public-action-blocked")
    return tuple(labels)


def _forbidden_actions(result: OAKBenchResult) -> tuple[str, ...]:
    forbidden = [
        "external_outreach_without_explicit_approval",
        "revenue_guarantee",
        "claim_beyond_evidence_level",
    ]
    if result.ip_review_required:
        forbidden.extend([
            "public_unredacted_ip_disclosure",
            "patent_filing_from_this_issue",
            "posting_private_source_urls",
        ])
    if not result.public_action_allowed:
        forbidden.append("public_automation_before_oak_gate_clearance")
    return tuple(dict.fromkeys(forbidden))


def build_github_issue_draft(signal: Signal, *, generated_at: str | None = None) -> GitHubIssueDraft:
    """Build a deterministic, public-safe GitHub issue draft.

    The issue body is derived from `OAKBenchResult` and redacted handoff/review
    packets. Sensitive IP routes use `handoff.safe_summary`, never raw signal
    summary or source URLs.
    """

    result = run_oakbench(signal, generated_at=generated_at)
    packet = result.review_packet
    handoff = packet.handoff
    intent = _intent(result)
    forbidden = _forbidden_actions(result)

    title_prefix = {
        "repair": "Ω Repair",
        "source_repair": "Ω Source Repair",
        "ip_review": "Ω IP Review",
        "prototype": "Ω Prototype",
        "commercial_validation": "Ω Commercial Validation",
        "observe": "Ω Observe",
    }[intent]
    title = f"{title_prefix} — {_slug_words(result.signal.title)}"

    source_block = _bullet_lines(tuple(handoff.source_urls))
    if result.ip_review_required or handoff.redacted:
        source_block = "- [REDACTED: sensitive IP route; use private review channel]"

    body = f"""## Ω OAKBench issue draft

Generated from a public-safe DeepTech Forge handoff packet.

### Decision

- Priority band: `{result.priority_band}`
- Action score: `{result.action_score}`
- Intent: `{intent}`
- OAK status: `{handoff.oak_status.value}`
- IP class: `{handoff.ip_class.value}`
- Evidence level: `{handoff.evidence_level.value}`
- Public action allowed: `{str(result.public_action_allowed).lower()}`
- IP review required: `{str(result.ip_review_required).lower()}`

### Public-safe summary

{handoff.safe_summary}

### Sources

{source_block}

### GitHub actions

{_checkbox_lines(result.github_actions)}

### Next actions

{_checkbox_lines(packet.next_actions)}

### OAK gates

{_bullet_lines(packet.gates)}

### Forbidden actions

{_bullet_lines(forbidden)}

### M⁻ negative memory

{_bullet_lines(result.m_minus)}

### Acceptance criteria

- [ ] Evidence and source status are reviewed.
- [ ] OAK status is not weakened manually.
- [ ] IP-sensitive details remain out of public GitHub artifacts.
- [ ] Prototype or commercial action has measurable validation criteria.
"""

    public_safe = not result.ip_review_required and handoff.ip_class not in {IPClass.PATENT_REVIEW, IPClass.TRADE_SECRET}
    if result.ip_review_required:
        public_safe = True  # still public-safe because body uses redacted handoff text only

    return GitHubIssueDraft(
        title=title,
        body=body,
        labels=_labels(result, intent),
        intent=intent,
        public_safe=public_safe,
        blocked_external_actions=forbidden,
    )


def build_many_github_issue_drafts(signals: list[Signal]) -> list[GitHubIssueDraft]:
    """Build public-safe drafts for many signals without network access."""

    return [build_github_issue_draft(signal) for signal in signals]
