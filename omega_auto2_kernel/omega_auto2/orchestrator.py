from __future__ import annotations

from dataclasses import dataclass

from .diff_report import diff_markdown
from .release import release_pipeline
from .snapshot import canonical_snapshot
from .sovereignty import human_sovereignty_check


@dataclass(frozen=True)
class OrchestratorResult:
    version: str
    status: str
    release_passed: bool
    sovereignty_passed: bool
    next_stage: str
    snapshot: dict[str, object]
    diff_markdown: str

    def to_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


def run_orchestrator(version: str = "1.0.0", actions: list[str] | None = None) -> OrchestratorResult:
    actions = actions or []
    sovereignty = human_sovereignty_check(actions)
    release = release_pipeline(version)
    passed = bool(release["passed"] and sovereignty.allowed)
    status = "release_candidate" if passed else "blocked"
    return OrchestratorResult(
        version=version,
        status=status,
        release_passed=bool(release["passed"]),
        sovereignty_passed=sovereignty.allowed,
        next_stage="manual_review_then_tag" if passed else "resolve_blockers",
        snapshot=canonical_snapshot(version),
        diff_markdown=diff_markdown(),
    )
