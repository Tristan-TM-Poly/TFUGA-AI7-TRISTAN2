"""Counterworld generator for Tristan AIT Reality Forge.

Generates structured worlds where an idea succeeds, fails, is abused, becomes
costly, hits limits, or is contradicted. This is for falsification planning, not
prediction certainty.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CounterworldKind(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    ABUSE = "abuse"
    COST = "cost"
    LIMIT = "limit"
    COUNTEREXAMPLE = "counterexample"


@dataclass(frozen=True)
class Counterworld:
    kind: CounterworldKind
    question: str
    scenario: str
    test_or_signal: str
    oak_response: str


@dataclass(frozen=True)
class CounterworldPack:
    idea: str
    worlds: tuple[Counterworld, ...]
    minimum_survival_rule: str


DEFAULT_QUESTIONS = {
    CounterworldKind.SUCCESS: "In what limited world does the idea work?",
    CounterworldKind.FAILURE: "In what world does the idea break?",
    CounterworldKind.ABUSE: "In what world is the idea misused?",
    CounterworldKind.COST: "In what world are hidden costs too high?",
    CounterworldKind.LIMIT: "Where does the idea stop applying?",
    CounterworldKind.COUNTEREXAMPLE: "What single case would weaken or falsify it?",
}


def generate_counterworlds(idea: str, *, high_stakes: bool = False) -> CounterworldPack:
    worlds: list[Counterworld] = []
    for kind, question in DEFAULT_QUESTIONS.items():
        oak_response = "document and test" if kind == CounterworldKind.SUCCESS else "add mitigation or falsification test"
        if high_stakes and kind in {CounterworldKind.ABUSE, CounterworldKind.COUNTEREXAMPLE}:
            oak_response = "quarantine or require qualified human validation"
        worlds.append(
            Counterworld(
                kind=kind,
                question=question,
                scenario=f"Counterworld for idea: {idea} / {kind.value}",
                test_or_signal=f"Define observable signal for {kind.value} world.",
                oak_response=oak_response,
            )
        )

    survival_rule = "The idea must expose failure, abuse, cost, limit, and counterexample tests before stronger claims."
    return CounterworldPack(idea=idea, worlds=tuple(worlds), minimum_survival_rule=survival_rule)
