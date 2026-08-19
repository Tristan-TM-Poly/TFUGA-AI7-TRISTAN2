"""Import Smoke Tester for Ω-AIT-SELF-STABILIZING-REFACTOR-KERNEL-T.

Builds a static import smoke plan. Planning only.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ImportSmokePlan:
    modules: tuple[str, ...]
    test_file: str
    next_safe_action: str


def build_import_smoke_plan(modules: tuple[str, ...], *, test_file: str = "tests/test_import_all_new_tools.py") -> ImportSmokePlan:
    unique = tuple(dict.fromkeys(module for module in modules if module.strip()))
    return ImportSmokePlan(
        modules=unique,
        test_file=test_file,
        next_safe_action="add static import smoke test before structural refactor",
    )
