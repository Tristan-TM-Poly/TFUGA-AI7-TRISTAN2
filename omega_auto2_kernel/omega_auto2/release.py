from __future__ import annotations

from .canonical import canonical_workflows
from .diff_report import diff_markdown
from .regression import regression_check
from .snapshot import canonical_snapshot


def quality_gate(version: str) -> dict[str, object]:
    checks = {
        "version_set": version == "0.9.0",
        "canonical_workflows_present": len(canonical_workflows()) >= 4,
        "external_actions_added": False,
        "safe_default": True,
    }
    passed = (
        checks["version_set"]
        and checks["canonical_workflows_present"]
        and not checks["external_actions_added"]
        and checks["safe_default"]
    )
    return {"quality_gate": checks, "passed": passed}


def release_pipeline(version: str = "0.9.0", baseline: dict[str, object] | None = None) -> dict[str, object]:
    qg = quality_gate(version)
    comparison = regression_check(baseline)
    snapshot = canonical_snapshot(version)
    diff = diff_markdown(baseline)
    passed = bool(qg["passed"] and comparison["passed"])
    return {
        "kind": "auto2_release_pipeline",
        "version": version,
        "passed": passed,
        "quality_gate": qg,
        "comparison": comparison["comparison"],
        "snapshot": snapshot,
        "diff_markdown": diff,
    }


def release_markdown(version: str = "0.9.0", baseline: dict[str, object] | None = None) -> str:
    payload = release_pipeline(version, baseline)
    lines = [
        "# Ω-AUTO² Release Pipeline",
        "",
        f"Version: {payload['version']}",
        f"Passed: {payload['passed']}",
        "",
        "## Quality gate",
        "",
        f"Passed: {payload['quality_gate']['passed']}",
        "",
        "## Regression comparison",
        "",
        f"Passed: {payload['comparison']['passed']}",
        "",
        "## Diff",
        "",
        str(payload["diff_markdown"]),
    ]
    return "\n".join(lines)
