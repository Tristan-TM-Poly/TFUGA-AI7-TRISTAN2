from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Mapping, Sequence

from .university_ir import CurriculumPlan, compile_curriculum


@dataclass(frozen=True)
class CurriculumOption:
    name: str
    declared_verified: tuple[str, ...] = ()
    declared_cost: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("option name must be a non-empty string")
        if self.name == "NONE":
            raise ValueError("NONE is reserved for the mandatory baseline")
        if self.declared_cost < 0:
            raise ValueError("declared_cost must be >= 0")


@dataclass(frozen=True)
class CurriculumCourtResult:
    option: str
    missing_count: int
    declared_cost: float
    ordered: tuple[str, ...]
    declared_verified: tuple[str, ...]
    rank_key: tuple[float, float, str]
    selected: bool
    authority: str = "COMPARE_ONLY"
    external_action_authorized: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def compare_curriculum_options(
    graph: Mapping[str, Sequence[str] | Iterable[str]],
    targets: Iterable[str],
    baseline_verified: Iterable[str] = (),
    options: Iterable[CurriculumOption] = (),
) -> tuple[CurriculumCourtResult, ...]:
    """Compare declared capability options against a mandatory NONE baseline.

    The court ranks structural plan length and caller-declared cost only. It does not
    claim that a shorter plan teaches better, that declared capabilities are real, or
    that the selected option should be executed.
    """

    baseline = tuple(sorted({str(x).strip() for x in baseline_verified if str(x).strip()}))
    option_rows = tuple(options)
    names = [row.name.strip() for row in option_rows]
    if len(names) != len(set(names)):
        raise ValueError("curriculum option names must be unique")

    compiled: list[tuple[str, float, tuple[str, ...], CurriculumPlan]] = []
    none_plan = compile_curriculum(graph, targets, verified=baseline)
    compiled.append(("NONE", 0.0, baseline, none_plan))

    for row in option_rows:
        verified = tuple(sorted(set(baseline).union(row.declared_verified)))
        plan = compile_curriculum(graph, targets, verified=verified)
        compiled.append((row.name.strip(), float(row.declared_cost), verified, plan))

    rank_keys = {
        name: (float(len(plan.missing)), cost, name)
        for name, cost, _verified, plan in compiled
    }
    best = min(rank_keys.values())

    return tuple(
        CurriculumCourtResult(
            option=name,
            missing_count=len(plan.missing),
            declared_cost=cost,
            ordered=plan.ordered,
            declared_verified=verified,
            rank_key=rank_keys[name],
            selected=rank_keys[name] == best,
        )
        for name, cost, verified, plan in sorted(compiled, key=lambda row: rank_keys[row[0]])
    )
