"""Canon routing and issue-factory helpers for Daily Omega War Room.

This module is intentionally side-effect free. It creates issue specifications,
branch routes, and memory notes, but it does not call the GitHub API directly.
That keeps OAK control and human approval before any public action.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sage_tristan.daily_omega_briefing import BriefingItem


KEYWORD_BRANCH_MAP: dict[str, tuple[str, ...]] = {
    "agent": ("Ω-AUTO²-T", "SAGE", "AIT", "Ω-CORP-JARVIS-T"),
    "automation": ("Ω-AUTO²-T", "SAGE", "AIT"),
    "workflow": ("Ω-AUTO²-T", "Ω-CORP-JARVIS-T"),
    "battery": ("Ω-BAT-T", "Ω-ENERGY-T"),
    "bms": ("Ω-BAT-T", "Ω-ENERGY-T"),
    "solar": ("Ω-OPT-SOLAR-T", "Ω-MFT-T", "Ω-ENERGY-T"),
    "optic": ("Ω-OPT-SOLAR-T", "Ω-OEMMTD-T", "Ω-LASER-MEMS-CPU-T"),
    "photon": ("Ω-OEMMTD-T", "Ω-LASER-MEMS-CPU-T"),
    "laser": ("Ω-LASER-MEMS-CPU-T", "Ω-MEMS-CPU-T"),
    "mems": ("Ω-MEMS-CPU-T", "Ω-LASER-MEMS-CPU-T"),
    "cpu": ("Ω-CPUFMT", "Ω-MEMS-CPU-T"),
    "chip": ("Ω-CPUFMT", "Ω-MEMS-CPU-T"),
    "circuit": ("Ω-CIRCUITS-T", "Ω-ENERGY-T"),
    "rlc": ("Ω-CIRCUITS-T",),
    "transformer": ("Ω-CIRCUITS-T", "Ω-ENERGY-T"),
    "plasma": ("Ω-PFT", "Ω-MECH-T", "Ω-OEMMTD-T"),
    "fluid": ("Ω-PFT", "Ω-MECH-T"),
    "turbulence": ("Ω-PFT", "Ω-TRANSFORM-T"),
    "wavelet": ("Ω-TRANSFORM-T", "Ω-FFWT-HAC-CVCD"),
    "ffwt": ("Ω-TRANSFORM-T", "Ω-FFWT-HAC-CVCD"),
    "spectroscopy": ("Ω-TRANSFORM-T", "Ω-FFWT-HAC-CVCD", "Ω-OEMMTD-T"),
    "patent": ("Ω-COMP-REV-IP-PUB-AUTOSEND", "Ω-CORP-JARVIS-T"),
    "ip": ("Ω-COMP-REV-IP-PUB-AUTOSEND", "Ω-CORP-JARVIS-T"),
    "grant": ("Ω-REVENUS", "Ω-CORP-JARVIS-T"),
    "funding": ("Ω-REVENUS", "Ω-CORP-JARVIS-T"),
    "startup": ("Ω-REVENUS", "Ω-CORP-JARVIS-T"),
    "quebec": ("Ω-REVENUS", "Ω-CORP-JARVIS-T", "Ω-AUTO²-T"),
    "canada": ("Ω-REVENUS", "Ω-CORP-JARVIS-T", "Ω-AUTO²-T"),
    "public sector": ("Ω-AUTO²-T", "Ω-PREUVE-T"),
}

TOPIC_DEFAULT_BRANCHES: dict[str, tuple[str, ...]] = {
    "ai_automation_agents": ("Ω-AUTO²-T", "SAGE", "AIT"),
    "physics_energy_materials": ("Ω-ENERGY-T", "Ω-OEMMTD-T", "Ω-MECH-T"),
    "quebec_canada_innovation": ("Ω-REVENUS", "Ω-CORP-JARVIS-T"),
    "startups_ip_revenues": ("Ω-COMP-REV-IP-PUB-AUTOSEND", "Ω-REVENUS"),
    "papers_patents": ("Ω-COMP-REV-IP-PUB-AUTOSEND", "Ω-TRANSFORM-T"),
    "world_tech_geopolitics": ("Ω-CORP-JARVIS-T", "Ω-REVENUS"),
}

LABELS_BY_TOPIC: dict[str, tuple[str, ...]] = {
    "ai_automation_agents": ("ai-agents", "automation"),
    "physics_energy_materials": ("energy-materials", "physics"),
    "quebec_canada_innovation": ("quebec-canada", "innovation"),
    "startups_ip_revenues": ("revenue-signal", "ip-review"),
    "papers_patents": ("paper-patent", "prior-art"),
    "world_tech_geopolitics": ("tech-geopolitics",),
}


@dataclass(frozen=True)
class RouteResult:
    """Canon routing result for one briefing item."""

    branches: tuple[str, ...]
    ip_classification: str
    issue_type: str
    m_plus: str
    m_minus: str


@dataclass(frozen=True)
class IssueSpec:
    """Side-effect-free GitHub issue candidate."""

    title: str
    body: str
    labels: tuple[str, ...]


def _item_text(item: BriefingItem) -> str:
    parts = [
        item.title,
        item.topic_anchor,
        " ".join(item.signal_type),
        item.why_it_matters,
        item.actionable_opportunity,
        item.business_funding_signal,
        item.ip_signal,
        item.next_action,
    ]
    parts.extend(source.title for source in item.sources)
    return " ".join(parts).lower()


def route_branches(item: BriefingItem, *, max_branches: int = 6) -> tuple[str, ...]:
    """Map one briefing item to Tristan canon branches."""

    text = _item_text(item)
    branches: list[str] = []

    def add_many(candidates: Iterable[str]) -> None:
        for branch in candidates:
            if branch not in branches:
                branches.append(branch)

    for keyword, mapped_branches in KEYWORD_BRANCH_MAP.items():
        if keyword in text:
            add_many(mapped_branches)

    add_many(TOPIC_DEFAULT_BRANCHES.get(item.topic_anchor, ()))
    return tuple(branches[:max_branches])


def classify_ip(item: BriefingItem) -> str:
    """Classify the safest IP/publication posture for an item."""

    text = _item_text(item)
    source_types = {source.source_type for source in item.sources}
    signal_types = set(item.signal_type)

    if "patent" in source_types or "patent" in signal_types:
        return "prior_art_review"
    if any(token in text for token in ("patentable", "invention", "trade secret", "licensing")):
        return "confidential_ip_review"
    if "paper" in source_types or "preprint" in source_types or "paper" in signal_types:
        return "publication_candidate"
    if any(token in text for token in ("grant", "funding", "customer", "procurement", "startup")):
        return "revenue_experiment"
    return "private_research"


def choose_issue_type(item: BriefingItem, ip_classification: str) -> str:
    """Choose the GitHub issue style produced by this signal."""

    signal_types = set(item.signal_type)
    if ip_classification in {"prior_art_review", "confidential_ip_review"}:
        return "IP / prior-art review"
    if "paper" in signal_types or "patent" in signal_types:
        return "Paper / patent digestion"
    if "funding" in signal_types or ip_classification == "revenue_experiment":
        return "Revenue / funding experiment"
    if item.final_score >= 25:
        return "Prototype candidate"
    return "OAK falsification note"


def route_item(item: BriefingItem) -> RouteResult:
    """Return full War Room routing metadata for one item."""

    branches = route_branches(item)
    ip_classification = classify_ip(item)
    issue_type = choose_issue_type(item, ip_classification)
    m_plus = f"Keep signal if it produces a testable action: {item.next_action}"
    m_minus = item.oak_check.m_minus_warning or item.oak_check.risk
    return RouteResult(
        branches=branches,
        ip_classification=ip_classification,
        issue_type=issue_type,
        m_plus=m_plus,
        m_minus=m_minus,
    )


def make_issue_labels(item: BriefingItem, route: RouteResult) -> tuple[str, ...]:
    """Create deterministic labels for a future GitHub issue."""

    labels: list[str] = ["omega-daily", "oak-check", "canon-router"]
    labels.extend(LABELS_BY_TOPIC.get(item.topic_anchor, ()))

    if "Prototype" in route.issue_type:
        labels.append("prototype-candidate")
    if "IP" in route.issue_type or route.ip_classification in {"prior_art_review", "confidential_ip_review"}:
        labels.append("ip-review")
    if "Revenue" in route.issue_type or route.ip_classification == "revenue_experiment":
        labels.append("revenue-signal")
    if route.m_minus:
        labels.append("m-minus")

    deduped: list[str] = []
    for label in labels:
        if label not in deduped:
            deduped.append(label)
    return tuple(deduped)


def make_issue_spec(item: BriefingItem) -> IssueSpec:
    """Convert one briefing item into a reviewable GitHub issue spec."""

    route = route_item(item)
    labels = make_issue_labels(item, route)
    sources = "\n".join(f"- {source.title} ({source.source_type}) — {source.url_or_identifier}" for source in item.sources)
    branches = ", ".join(route.branches) if route.branches else "Unrouted"

    body = f"""## Signal

{item.why_it_matters}

## Actionable opportunity

{item.actionable_opportunity}

## Canon branches

{branches}

## OAK check

- Claim status: {item.oak_check.claim_status}
- Risk: {item.oak_check.risk}
- Limit: {item.oak_check.limit or 'Not specified'}
- Falsification route: {item.oak_check.falsification_route}

## IP / revenue posture

- Classification: {route.ip_classification}
- IP signal: {item.ip_signal or 'None specified'}
- Business/funding signal: {item.business_funding_signal or 'None specified'}

## Sources

{sources}

## M+ / M-

- M+: {route.m_plus}
- M-: {route.m_minus}

## Definition of done

- [ ] Source is checked.
- [ ] OAK risk is updated.
- [ ] Minimal test or prior-art search is defined.
- [ ] Decision is made: reject, prototype, publish, protect, or canonize.
"""

    title = f"[{route.issue_type}] {item.title}"
    return IssueSpec(title=title, body=body, labels=labels)


def render_war_room_markdown(items: Iterable[BriefingItem]) -> str:
    """Render canon routing and issue-factory output for a list of ranked items."""

    lines = ["# Daily Ω War Room", ""]
    for item in items:
        route = route_item(item)
        issue = make_issue_spec(item)
        rank = item.rank if item.rank is not None else "?"
        lines.extend(
            [
                f"## {rank}. {item.title}",
                f"- **Canon branches:** {', '.join(route.branches)}",
                f"- **Issue type:** {route.issue_type}",
                f"- **IP posture:** {route.ip_classification}",
                f"- **Labels:** {', '.join(issue.labels)}",
                f"- **M+:** {route.m_plus}",
                f"- **M-:** {route.m_minus}",
                f"- **Recommended issue title:** {issue.title}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


__all__ = [
    "IssueSpec",
    "RouteResult",
    "classify_ip",
    "choose_issue_type",
    "make_issue_labels",
    "make_issue_spec",
    "render_war_room_markdown",
    "route_branches",
    "route_item",
]
