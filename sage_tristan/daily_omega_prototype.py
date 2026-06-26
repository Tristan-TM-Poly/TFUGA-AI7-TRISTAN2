"""PrototypeCompiler for Daily Omega Intelligence OS.

This module converts compiled SignalGenome++ objects into OAK-safe prototype
plans. A plan is a ladder from P0 to P4 with explicit artifacts, success
metrics, estimated effort, and blockers.

It is local-only: no network calls, no GitHub calls, no issue creation, no
external actions, and no canon promotion.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable

from sage_tristan.daily_omega_batch import DEFAULT_TIMEZONE, build_batch_from_directory
from sage_tristan.daily_omega_evidence import EvidenceGraph, build_evidence_graph
from sage_tristan.daily_omega_intelligence_os import SignalGenome


@dataclass(frozen=True)
class PrototypeStep:
    """One prototype step in the P0..P4 ladder."""

    level: str
    horizon: str
    objective: str
    artifact: str
    success_metric: str
    oak_gate: str
    allowed_public: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "horizon": self.horizon,
            "objective": self.objective,
            "artifact": self.artifact,
            "success_metric": self.success_metric,
            "oak_gate": self.oak_gate,
            "allowed_public": self.allowed_public,
        }


@dataclass(frozen=True)
class PrototypePlan:
    """OAK-safe prototype plan for one signal."""

    signal_title: str
    prototype_horizon: str
    recommended_start: str
    blockers: tuple[str, ...]
    steps: tuple[PrototypeStep, ...]
    m_minus: str

    @property
    def can_start(self) -> bool:
        return not self.blockers or self.recommended_start == "P0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_title": self.signal_title,
            "prototype_horizon": self.prototype_horizon,
            "recommended_start": self.recommended_start,
            "can_start": self.can_start,
            "blockers": list(self.blockers),
            "steps": [step.to_dict() for step in self.steps],
            "m_minus": self.m_minus,
        }


@dataclass(frozen=True)
class PrototypeResult:
    """Batch-level prototype plan export."""

    briefing_date: date
    timezone: str
    plans: tuple[PrototypePlan, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "briefing_date": self.briefing_date.isoformat(),
            "timezone": self.timezone,
            "plans": [plan.to_dict() for plan in self.plans],
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


def _dedupe(values: Iterable[str]) -> tuple[str, ...]:
    deduped: list[str] = []
    for value in values:
        if value and value not in deduped:
            deduped.append(value)
    return tuple(deduped)


def collect_prototype_blockers(genome: SignalGenome, evidence_graph: EvidenceGraph) -> tuple[str, ...]:
    """Collect blockers that constrain prototype scope."""

    blockers: list[str] = []
    blockers.extend(evidence_graph.promotion_blockers)
    if genome.oak_validation_route.blocking_check != "none":
        blockers.append(genome.oak_validation_route.blocking_check)
    if genome.ip_risk_level in {"high_confidential_invention", "danger_do_not_disclose"}:
        blockers.append("private_only_ip_review")
    if genome.agent_security_ledger.permission_scope != "none":
        blockers.append("agent_safety_dry_run_only")
    if genome.infrastructure_dependency.risk_level == "high":
        blockers.append("infrastructure_assumption_check")
    return _dedupe(blockers)


def recommended_start_level(blockers: tuple[str, ...], genome: SignalGenome) -> str:
    """Recommend the safest starting step."""

    if "claim_support_gap" in blockers or "source_upgrade_check" in blockers:
        return "P0"
    if "private_only_ip_review" in blockers:
        return "P0"
    if genome.prototype_horizon in {"2_hour", "1_day", "1_week"}:
        return "P1"
    return "P0"


def public_allowed_for_step(step_level: str, blockers: tuple[str, ...]) -> bool:
    """Return whether a step artifact is safe for public-facing output."""

    if "private_only_ip_review" in blockers:
        return False
    if step_level in {"P3", "P4"} and blockers:
        return False
    return True


def build_prototype_steps(genome: SignalGenome, blockers: tuple[str, ...]) -> tuple[PrototypeStep, ...]:
    """Build the canonical P0..P4 prototype ladder."""

    private_prefix = "private_" if "private_only_ip_review" in blockers else ""
    step_specs = [
        (
            "P0",
            "15_min",
            genome.prototype_ladder.p0_15_min,
            f"{private_prefix}source_note.md",
            "All central claims have at least one review-ready source or an explicit M- rejection note.",
            "source_check",
        ),
        (
            "P1",
            "2_hour",
            genome.prototype_ladder.p1_2_hour,
            f"{private_prefix}oakbench_stub.py",
            "The local stub runs and emits a minimal JSON result without external side effects.",
            "dry_run_check",
        ),
        (
            "P2",
            "1_day",
            genome.prototype_ladder.p2_1_day,
            f"{private_prefix}evidence_report.md + {private_prefix}evidence.json",
            "The prototype produces reproducible Markdown and JSON evidence on one example batch.",
            "reproducibility_check",
        ),
        (
            "P3",
            "1_week",
            genome.prototype_ladder.p3_1_week,
            f"{private_prefix}benchmark_result.json",
            "The prototype is compared against a baseline, manual workflow, or no-action option.",
            "baseline_check",
        ),
        (
            "P4",
            "1_month",
            genome.prototype_ladder.p4_1_month,
            f"{private_prefix}offer_or_ip_one_pager.md",
            "A service, software, dataset, grant, publication, or IP route is selected with explicit limits.",
            "ip_revenue_check",
        ),
    ]
    return tuple(
        PrototypeStep(
            level=level,
            horizon=horizon,
            objective=objective,
            artifact=artifact,
            success_metric=success_metric,
            oak_gate=oak_gate,
            allowed_public=public_allowed_for_step(level, blockers),
        )
        for level, horizon, objective, artifact, success_metric, oak_gate in step_specs
    )


def build_prototype_plan(genome: SignalGenome, *, evidence_graph: EvidenceGraph | None = None) -> PrototypePlan:
    """Build one OAK-safe prototype plan."""

    graph = evidence_graph or build_evidence_graph(genome)
    blockers = collect_prototype_blockers(genome, graph)
    return PrototypePlan(
        signal_title=genome.title,
        prototype_horizon=genome.prototype_horizon,
        recommended_start=recommended_start_level(blockers, genome),
        blockers=blockers,
        steps=build_prototype_steps(genome, blockers),
        m_minus=genome.m_minus,
    )


def build_prototype_result(
    genomes: Iterable[SignalGenome],
    *,
    briefing_date: date,
    timezone: str = DEFAULT_TIMEZONE,
) -> PrototypeResult:
    """Build prototype plans from compiled genomes."""

    return PrototypeResult(
        briefing_date=briefing_date,
        timezone=timezone,
        plans=tuple(build_prototype_plan(genome) for genome in genomes),
    )


def build_prototype_from_directory(
    directory: str,
    *,
    briefing_date: date,
    timezone: str = DEFAULT_TIMEZONE,
    limit: int = 5,
    dry_run: bool = True,
) -> PrototypeResult:
    """Load signals, compile genomes, and return prototype plans."""

    batch = build_batch_from_directory(
        directory,
        briefing_date=briefing_date,
        timezone=timezone,
        limit=limit,
        dry_run=dry_run,
    )
    return build_prototype_result(batch.genomes, briefing_date=briefing_date, timezone=timezone)


def render_prototype_markdown(result: PrototypeResult) -> str:
    """Render prototype plans as Markdown."""

    lines = [
        f"# Daily Ω PrototypeCompiler — {result.briefing_date.isoformat()}",
        "",
        f"Timezone: `{result.timezone}`",
        "",
    ]
    for index, plan in enumerate(result.plans, start=1):
        lines.extend(
            [
                f"## {index}. {plan.signal_title}",
                f"- **Prototype horizon:** `{plan.prototype_horizon}`",
                f"- **Recommended start:** `{plan.recommended_start}`",
                f"- **Can start:** `{str(plan.can_start).lower()}`",
                f"- **Blockers:** {', '.join(plan.blockers) or 'none'}",
                f"- **M-:** {plan.m_minus}",
                "",
                "### Ladder",
                "",
            ]
        )
        for step in plan.steps:
            lines.extend(
                [
                    f"- **{step.level} / {step.horizon}:** {step.objective}",
                    f"  - artifact: `{step.artifact}`",
                    f"  - success: {step.success_metric}",
                    f"  - OAK gate: `{step.oak_gate}`",
                    f"  - public allowed: `{str(step.allowed_public).lower()}`",
                ]
            )
        lines.append("")
    return "\n".join(lines)


__all__ = [
    "PrototypePlan",
    "PrototypeResult",
    "PrototypeStep",
    "build_prototype_from_directory",
    "build_prototype_plan",
    "build_prototype_result",
    "build_prototype_steps",
    "collect_prototype_blockers",
    "public_allowed_for_step",
    "recommended_start_level",
    "render_prototype_markdown",
]
