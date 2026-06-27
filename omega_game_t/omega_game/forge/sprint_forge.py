"""SprintForge-T for Ω-GAME-T++.

Convert IssueSet roadmaps into prioritized sprint plans. This module does not
create calendar events, remote tasks, or external project-board changes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .issue_forge import IssueSet, IssueSpec


@dataclass(slots=True)
class SprintTask:
    task_id: str
    title: str
    source_issue_title: str
    priority: str
    estimate_points: int
    execution_order: int
    acceptance_criteria: list[str]
    oak_gates: list[str]
    definition_of_done: list[str]
    positive_memory_expected: list[str] = field(default_factory=list)
    negative_memory_avoided: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.priority not in {"p0", "p1", "p2"}:
            raise ValueError("SprintTask.priority must be one of p0, p1, p2.")
        if self.estimate_points <= 0:
            raise ValueError("SprintTask.estimate_points must be positive.")
        if self.execution_order <= 0:
            raise ValueError("SprintTask.execution_order must be positive.")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class SprintPlan:
    name: str
    source_epic: str
    source_theory: str
    target_engine: str
    cadence: str
    total_points: int
    tasks: list[SprintTask]
    oak_gates: list[str]
    definition_of_done: list[str]

    def __post_init__(self) -> None:
        if not self.tasks:
            raise ValueError("SprintPlan.tasks must be non-empty.")
        if self.total_points <= 0:
            raise ValueError("SprintPlan.total_points must be positive.")

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "source_epic": self.source_epic,
            "source_theory": self.source_theory,
            "target_engine": self.target_engine,
            "cadence": self.cadence,
            "total_points": self.total_points,
            "tasks": [task.to_dict() for task in self.tasks],
            "oak_gates": list(self.oak_gates),
            "definition_of_done": list(self.definition_of_done),
        }

    def to_markdown(self) -> str:
        tasks_md = "\n".join(
            f"{task.execution_order}. [{task.priority.upper()}] {task.title} ({task.estimate_points} pts)"
            for task in self.tasks
        )
        gates = "\n".join(f"- [ ] {gate}" for gate in self.oak_gates)
        dod = "\n".join(f"- [ ] {item}" for item in self.definition_of_done)
        return (
            f"# {self.name}\n\n"
            f"Epic: `{self.source_epic}`\n\n"
            f"Theory: `{self.source_theory}`\n\n"
            f"Engine: `{self.target_engine}`\n\n"
            f"Cadence: `{self.cadence}`\n\n"
            f"Total points: `{self.total_points}`\n\n"
            f"## Tasks\n\n{tasks_md}\n\n"
            f"## OAK gates\n\n{gates}\n\n"
            f"## Definition of Done\n\n{dod}\n"
        )


class SprintForge:
    """Generate prioritized sprint plans from IssueSet objects."""

    def forge(self, issue_set: IssueSet, cadence: str = "7_days") -> SprintPlan:
        ordered_issues = sorted(issue_set.issues, key=self._issue_sort_key)
        tasks = [self._task_from_issue(issue, index + 1) for index, issue in enumerate(ordered_issues)]
        total_points = sum(task.estimate_points for task in tasks)
        return SprintPlan(
            name=f"{issue_set.target_engine} MVP Sprint",
            source_epic=issue_set.epic_title,
            source_theory=issue_set.source_theory,
            target_engine=issue_set.target_engine,
            cadence=cadence,
            total_points=total_points,
            tasks=tasks,
            oak_gates=self._sprint_oak_gates(issue_set),
            definition_of_done=self._definition_of_done(),
        )

    def forge_many(self, issue_sets: list[IssueSet], cadence: str = "7_days") -> list[SprintPlan]:
        return [self.forge(issue_set, cadence=cadence) for issue_set in issue_sets]

    def _task_from_issue(self, issue: IssueSpec, execution_order: int) -> SprintTask:
        return SprintTask(
            task_id=f"task_{execution_order:02d}_{self._slug(issue.title)}",
            title=self._task_title(issue),
            source_issue_title=issue.title,
            priority=issue.priority,
            estimate_points=self._estimate_points(issue),
            execution_order=execution_order,
            acceptance_criteria=list(issue.acceptance_criteria),
            oak_gates=list(issue.oak_controls),
            definition_of_done=self._definition_of_done(),
            positive_memory_expected=list(issue.positive_memory_expected),
            negative_memory_avoided=list(issue.negative_memory_avoided),
        )

    def _task_title(self, issue: IssueSpec) -> str:
        if issue.title.startswith("Add "):
            return issue.title.replace("Add ", "Implement ", 1)
        if issue.title.startswith("Prepare "):
            return issue.title
        if issue.title.startswith("Reduce "):
            return issue.title
        return f"Complete {issue.title}"

    def _estimate_points(self, issue: IssueSpec) -> int:
        base = {"p0": 5, "p1": 3, "p2": 2}[issue.priority]
        if any("type:bench" in label for label in issue.labels):
            base += 2
        if any("type:oak" in label for label in issue.labels):
            base += 1
        if len(issue.acceptance_criteria) > 3:
            base += 1
        return base

    def _issue_sort_key(self, issue: IssueSpec) -> tuple[int, int, str]:
        priority_rank = {"p0": 0, "p1": 1, "p2": 2}[issue.priority]
        label_rank = 0
        if any("type:bench" in label for label in issue.labels):
            label_rank = -2
        elif any("type:oak" in label for label in issue.labels):
            label_rank = -1
        elif any("launch-draft" in label for label in issue.labels):
            label_rank = 2
        return (priority_rank, label_rank, issue.title)

    def _sprint_oak_gates(self, issue_set: IssueSet) -> list[str]:
        gates = [
            "all_p0_tasks_completed_or_explicitly_deferred",
            "tests_or_validation_notes_present",
            "limits_and_assumptions_visible",
            "no_external_release_from_sprint_plan",
            "m_plus_and_m_minus_notes_present",
        ]
        if any("ip-review" in label for label in issue_set.label_plan.labels):
            gates.append("ip_review_status_visible")
        return gates

    @staticmethod
    def _definition_of_done() -> list[str]:
        return [
            "implementation_or_documentation_added",
            "tests_or_validation_notes_added",
            "README_or_demo_updated_if_relevant",
            "OAK_controls_checked",
            "M_plus_expected_and_M_minus_avoided_recorded",
        ]

    @staticmethod
    def _slug(value: str) -> str:
        return "_".join("".join(char.lower() if char.isalnum() else " " for char in value).split())[:80]


def default_sprint_forge() -> SprintForge:
    return SprintForge()


__all__ = ["SprintForge", "SprintPlan", "SprintTask", "default_sprint_forge"]
