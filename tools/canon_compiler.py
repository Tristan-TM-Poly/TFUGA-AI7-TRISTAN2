"""Canon Compiler for Tristan CanonOS.

Compiles a canon branch into a repository-ready package plan. This module plans
artifacts only; it does not publish, merge, deploy, or alter external systems.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CanonPackagePlan:
    branch_name: str
    directories: tuple[str, ...]
    required_files: tuple[str, ...]
    safe_next_action: str


def compile_canon_package(branch_name: str, *, include_benchmarks: bool = False, include_examples: bool = True) -> CanonPackagePlan:
    slug = "".join(ch.lower() if ch.isalnum() else "_" for ch in branch_name).strip("_") or "canon_branch"
    directories = [
        "docs/theories",
        "schemas",
        "tools",
        "tests",
        "safety",
        "docs/oak_reports",
        "docs/roadmaps",
    ]
    if include_benchmarks:
        directories.append("benchmarks")
    if include_examples:
        directories.append("examples")

    required_files = (
        f"docs/theories/{slug}.md",
        f"schemas/{slug}.schema.json",
        f"tools/{slug}.py",
        f"tests/test_{slug}.py",
        f"safety/m_minus_{slug}.yaml",
        f"docs/oak_reports/{slug}_oak_report.md",
        f"docs/roadmaps/{slug}_top64.md",
    )

    return CanonPackagePlan(
        branch_name=slug,
        directories=tuple(directories),
        required_files=required_files,
        safe_next_action="Create files on a reversible branch or draft PR; do not auto-merge.",
    )
