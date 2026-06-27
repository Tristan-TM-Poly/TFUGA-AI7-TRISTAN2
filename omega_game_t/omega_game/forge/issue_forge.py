"""IssueForge-T for Ω-GAME-T++.

Generate GitHub-ready issue roadmaps from ProductPlan objects. This module does
not create remote GitHub issues; it only emits serializable issue specs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from re import sub

from ..productizer import ProductPlan


@dataclass(slots=True)
class LabelPlan:
    labels: list[str]

    def __post_init__(self) -> None:
        if not self.labels:
            raise ValueError("LabelPlan.labels must be non-empty.")

    def to_dict(self) -> dict[str, object]:
        return {"labels": list(dict.fromkeys(self.labels))}


@dataclass(slots=True)
class MilestonePlan:
    title: str
    description: str

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("MilestonePlan.title must be non-empty.")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class IssueSpec:
    title: str
    body: str
    labels: list[str]
    acceptance_criteria: list[str]
    oak_controls: list[str]
    positive_memory_expected: list[str]
    negative_memory_avoided: list[str]
    priority: str = "p1"

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("IssueSpec.title must be non-empty.")
        if self.priority not in {"p0", "p1", "p2"}:
            raise ValueError("IssueSpec.priority must be one of p0, p1, p2.")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def to_markdown(self) -> str:
        criteria = "\n".join(f"- [ ] {item}" for item in self.acceptance_criteria)
        controls = "\n".join(f"- [ ] {item}" for item in self.oak_controls)
        positive = "\n".join(f"- {item}" for item in self.positive_memory_expected)
        negative = "\n".join(f"- {item}" for item in self.negative_memory_avoided)
        labels = ", ".join(self.labels)
        return (
            f"# {self.title}\n\n"
            f"{self.body}\n\n"
            f"## Labels\n\n{labels}\n\n"
            f"## Priority\n\n{self.priority}\n\n"
            f"## Acceptance criteria\n\n{criteria}\n\n"
            f"## OAK controls\n\n{controls}\n\n"
            f"## M+ expected\n\n{positive}\n\n"
            f"## M- avoided\n\n{negative}\n"
        )


@dataclass(slots=True)
class IssueSet:
    epic_title: str
    source_theory: str
    target_engine: str
    product_name: str
    milestone: MilestonePlan
    label_plan: LabelPlan
    issues: list[IssueSpec]

    def __post_init__(self) -> None:
        if not self.issues:
            raise ValueError("IssueSet.issues must be non-empty.")

    def to_dict(self) -> dict[str, object]:
        return {
            "epic_title": self.epic_title,
            "source_theory": self.source_theory,
            "target_engine": self.target_engine,
            "product_name": self.product_name,
            "milestone": self.milestone.to_dict(),
            "label_plan": self.label_plan.to_dict(),
            "issues": [issue.to_dict() for issue in self.issues],
        }

    def to_markdown(self) -> str:
        issue_blocks = "\n\n---\n\n".join(issue.to_markdown() for issue in self.issues)
        return (
            f"# {self.epic_title}\n\n"
            f"Source theory: `{self.source_theory}`\n\n"
            f"Target engine: `{self.target_engine}`\n\n"
            f"Product: `{self.product_name}`\n\n"
            f"Milestone: `{self.milestone.title}`\n\n"
            f"Labels: {', '.join(self.label_plan.labels)}\n\n"
            f"---\n\n{issue_blocks}\n"
        )


class IssueForge:
    """Generate issue specifications from ProductPlan objects."""

    def forge(self, plan: ProductPlan) -> IssueSet:
        labels = self._labels_for(plan)
        milestone = MilestonePlan(
            title=f"{plan.target_engine} MVP",
            description=f"Roadmap for {plan.product_name} generated from {plan.source_theory}.",
        )
        issues: list[IssueSpec] = []
        issues.extend(self._deliverable_issues(plan, labels))
        issues.append(self._oakbench_issue(plan, labels))
        issues.append(self._risk_issue(plan, labels))
        issues.append(self._launch_readiness_issue(plan, labels))
        return IssueSet(
            epic_title=f"Build {plan.product_name}",
            source_theory=plan.source_theory,
            target_engine=plan.target_engine,
            product_name=plan.product_name,
            milestone=milestone,
            label_plan=LabelPlan(labels=labels),
            issues=issues,
        )

    def forge_many(self, plans: list[ProductPlan]) -> list[IssueSet]:
        return [self.forge(plan) for plan in plans]

    def _deliverable_issues(self, plan: ProductPlan, base_labels: list[str]) -> list[IssueSpec]:
        issues = []
        for index, deliverable in enumerate(plan.deliverables, start=1):
            human = deliverable.replace("_", " ")
            issues.append(
                IssueSpec(
                    title=f"Add {human} for {plan.product_name}",
                    body=self._body(plan, value=f"Create deliverable `{deliverable}` for the product MVP."),
                    labels=base_labels + ["type:deliverable", self._slug_label("deliverable", deliverable)],
                    acceptance_criteria=[
                        f"Deliverable `{deliverable}` is represented in docs or code",
                        "Relevant tests or validation notes are added",
                        "README or demo path references the deliverable",
                    ],
                    oak_controls=plan.oak_controls,
                    positive_memory_expected=[f"deliverable_{deliverable}_completed"],
                    negative_memory_avoided=plan.risks or ["unclear_scope"],
                    priority="p0" if index == 1 else "p1",
                )
            )
        return issues

    def _oakbench_issue(self, plan: ProductPlan, base_labels: list[str]) -> IssueSpec:
        return IssueSpec(
            title=f"Add OAKBench/ProductBench report for {plan.product_name}",
            body=self._body(plan, value="Make product quality measurable before launch."),
            labels=base_labels + ["type:bench", "oak-safe"],
            acceptance_criteria=[
                "OAKBench or ProductBench metrics are listed",
                "Score output is serialized or documented",
                "Limits and assumptions are visible",
            ],
            oak_controls=plan.oak_controls,
            positive_memory_expected=["bench_report_completed", "quality_signal_visible"],
            negative_memory_avoided=["unmeasured_launch", "overclaim"],
            priority="p0",
        )

    def _risk_issue(self, plan: ProductPlan, base_labels: list[str]) -> IssueSpec:
        risks = plan.risks or ["unknown_risk"]
        return IssueSpec(
            title=f"Reduce top OAK risks for {plan.product_name}",
            body=self._body(plan, value=f"Reduce known risks: {', '.join(risks)}."),
            labels=base_labels + ["type:oak", "oak-risk"],
            acceptance_criteria=[
                "Top risks are listed",
                "Each risk has a mitigation note",
                "Human review gate is documented if needed",
            ],
            oak_controls=plan.oak_controls,
            positive_memory_expected=["risk_register_created", "mitigation_visible"],
            negative_memory_avoided=risks,
            priority="p0",
        )

    def _launch_readiness_issue(self, plan: ProductPlan, base_labels: list[str]) -> IssueSpec:
        return IssueSpec(
            title=f"Prepare launch-readiness checklist for {plan.product_name}",
            body=self._body(plan, value="Prepare an internal launch checklist without external publication."),
            labels=base_labels + ["type:product", "launch-draft"],
            acceptance_criteria=[
                "Launch steps are written as checklist items",
                "IP/public-release review status is visible",
                "No external publication is performed by the issue itself",
            ],
            oak_controls=plan.oak_controls,
            positive_memory_expected=["launch_checklist_ready"],
            negative_memory_avoided=["premature_release", "missing_review"],
            priority="p1",
        )

    def _body(self, plan: ProductPlan, value: str) -> str:
        revenue_paths = ", ".join(plan.revenue_paths)
        audience = ", ".join(plan.audience)
        return (
            f"## Product\n\n{plan.product_name}\n\n"
            f"## Source theory\n\n{plan.source_theory}\n\n"
            f"## Target engine\n\n{plan.target_engine}\n\n"
            f"## Value\n\n{value}\n\n"
            f"## Audience\n\n{audience}\n\n"
            f"## Revenue paths\n\n{revenue_paths}\n\n"
            f"## IP status\n\n{plan.ip_classification}\n"
        )

    def _labels_for(self, plan: ProductPlan) -> list[str]:
        labels = [
            "omega-game-t",
            "product",
            "oak-safe",
            self._slug_label("engine", plan.target_engine),
            self._slug_label("theory", plan.source_theory),
        ]
        if "Lesson" in plan.product_name or "Training" in plan.product_name:
            labels.append("education")
        if plan.revenue_paths:
            labels.append("revenue")
        if "review" in plan.ip_classification:
            labels.append("ip-review")
        return list(dict.fromkeys(labels))

    @staticmethod
    def _slug_label(prefix: str, value: str) -> str:
        cleaned = sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
        return f"{prefix}:{cleaned or 'unknown'}"


def default_issue_forge() -> IssueForge:
    return IssueForge()


__all__ = ["IssueForge", "IssueSet", "IssueSpec", "LabelPlan", "MilestonePlan", "default_issue_forge"]
