"""M-minus registry for Omega absorb v1.4."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class MMinusEntry:
    error: str
    rule: str
    fix: str
    status: str


@dataclass(frozen=True)
class MMinusRegistry:
    entries: Tuple[MMinusEntry, ...]
    next_action: str


def default_mminus_registry() -> MMinusRegistry:
    entries = (
        MMinusEntry(
            error="strict version assertion broke future CLI tests",
            rule="tests should assert semantic compatibility instead of fixed current version",
            fix="assert version output starts with omega-absorb and keep exact version tests only for current release",
            status="canonized",
        ),
        MMinusEntry(
            error="long branch names or detailed PR bodies may trigger connector friction",
            rule="use short branch names and concise PR bodies",
            fix="prefer workNN branches and short summaries",
            status="canonized",
        ),
        MMinusEntry(
            error="source validation can reject useful demo records when schemas are too strict",
            rule="separate blocked restricted fields from warnings for unknown metadata fields",
            fix="strict schema blocks restricted fields and required-field errors, while unknown fields become warnings",
            status="canonized",
        ),
    )
    return MMinusRegistry(entries=entries, next_action="inject_mminus_rules_into_next_packets")


def render_mminus_markdown(registry: MMinusRegistry | None = None) -> str:
    registry = registry or default_mminus_registry()
    lines = ["# Omega Absorb M-minus Registry", ""]
    for index, entry in enumerate(registry.entries, start=1):
        lines.extend(
            [
                f"## {index}. {entry.error}",
                f"- rule: {entry.rule}",
                f"- fix: {entry.fix}",
                f"- status: {entry.status}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"
