"""Department strategy matrix for Omega absorb v1.7."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from .professor_tensor import ProfessorTensor


@dataclass(frozen=True)
class DepartmentStrategyCell:
    department: str
    teaching_weight: float
    prototype_weight: float
    bridge_weight: float
    ip_weight: float
    risk_weight: float
    next_action: str


@dataclass(frozen=True)
class DepartmentStrategyMatrix:
    cells: Tuple[DepartmentStrategyCell, ...]
    next_action: str


def build_department_strategy_matrix(tensors: Iterable[ProfessorTensor]) -> DepartmentStrategyMatrix:
    buckets: dict[str, dict[str, float]] = {}
    counts: dict[str, int] = {}
    for tensor in tensors:
        departments = tensor.departments or ("unknown",)
        for dept in departments:
            bucket = buckets.setdefault(dept, {"teaching": 0.0, "prototype": 0.0, "bridge": 0.0, "ip": 0.0, "risk": 0.0})
            counts[dept] = counts.get(dept, 0) + 1
            bucket["teaching"] += len(tensor.teaching)
            bucket["prototype"] += len(tensor.projects) + len(tensor.methods)
            bucket["bridge"] += len(tensor.collaboration_vector)
            bucket["ip"] += len(tensor.ip_signals)
            bucket["risk"] += len(tensor.risks)
    cells = []
    for dept, bucket in sorted(buckets.items()):
        count = max(1, counts[dept])
        cells.append(
            DepartmentStrategyCell(
                department=dept,
                teaching_weight=round(min(1.0, 0.25 + 0.08 * bucket["teaching"] / count), 4),
                prototype_weight=round(min(1.0, 0.25 + 0.06 * bucket["prototype"] / count), 4),
                bridge_weight=round(min(1.0, 0.25 + 0.04 * bucket["bridge"] / count), 4),
                ip_weight=round(min(1.0, 0.20 + 0.08 * bucket["ip"] / count), 4),
                risk_weight=round(min(1.0, 0.10 + 0.08 * bucket["risk"] / count), 4),
                next_action="route_department_strategy_cell",
            )
        )
    return DepartmentStrategyMatrix(tuple(cells), "rank_department_strategy_cells")


def render_department_strategy_matrix(matrix: DepartmentStrategyMatrix) -> str:
    lines = ["department | teaching | prototype | bridge | ip | risk", "--- | --- | --- | --- | --- | ---"]
    for cell in matrix.cells:
        lines.append(f"{cell.department} | {cell.teaching_weight:.4f} | {cell.prototype_weight:.4f} | {cell.bridge_weight:.4f} | {cell.ip_weight:.4f} | {cell.risk_weight:.4f}")
    return "\n".join(lines) + "\n"
