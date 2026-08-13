from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import isfinite
from typing import Any, Iterable, Mapping

from omega_capability_os_t.core import stable_digest


STAGE_ORDER = ("direct", "capability_os", "cognitive_capability", "ttm_exec")
ABLATION_CHAIN = (
    ("capability_os", "capability_os", "direct"),
    ("cognitive_computer", "cognitive_capability", "capability_os"),
    ("ttm_exec", "ttm_exec", "cognitive_capability"),
)


@dataclass(frozen=True)
class StageMeasurement:
    """Measured outcome for one architecture on the same benchmark case.

    Benefit axes are maximized; burden axes are minimized. Values are deliberately
    not scalarized so TTMBench can expose trade-offs instead of hiding them behind
    an arbitrary universal utility function.
    """

    stage: str
    task_success: float
    evidence_strength: float
    reuse: float
    robustness: float
    information_gain: float
    cost: float
    latency: float
    complexity: float
    human_attention: float
    risk: float
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.stage.strip():
            raise ValueError("stage cannot be empty")
        for name, value in self.numeric_axes().items():
            if not isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and non-negative")

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "StageMeasurement":
        return cls(
            stage=str(raw["stage"]),
            task_success=float(raw["task_success"]),
            evidence_strength=float(raw["evidence_strength"]),
            reuse=float(raw["reuse"]),
            robustness=float(raw["robustness"]),
            information_gain=float(raw["information_gain"]),
            cost=float(raw["cost"]),
            latency=float(raw["latency"]),
            complexity=float(raw["complexity"]),
            human_attention=float(raw["human_attention"]),
            risk=float(raw["risk"]),
            metadata=dict(raw.get("metadata") or {}),
        )

    def benefit_axes(self) -> dict[str, float]:
        return {
            "task_success": self.task_success,
            "evidence_strength": self.evidence_strength,
            "reuse": self.reuse,
            "robustness": self.robustness,
            "information_gain": self.information_gain,
        }

    def burden_axes(self) -> dict[str, float]:
        return {
            "cost": self.cost,
            "latency": self.latency,
            "complexity": self.complexity,
            "human_attention": self.human_attention,
            "risk": self.risk,
        }

    def numeric_axes(self) -> dict[str, float]:
        return {**self.benefit_axes(), **self.burden_axes()}

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(self.metadata)
        return payload


def dominates(left: StageMeasurement, right: StageMeasurement) -> bool:
    """Strict Pareto dominance: all benefits >=, all burdens <=, at least one strict."""

    left_benefits = left.benefit_axes()
    right_benefits = right.benefit_axes()
    left_burdens = left.burden_axes()
    right_burdens = right.burden_axes()
    weak = all(left_benefits[k] >= right_benefits[k] for k in left_benefits) and all(
        left_burdens[k] <= right_burdens[k] for k in left_burdens
    )
    strict = any(left_benefits[k] > right_benefits[k] for k in left_benefits) or any(
        left_burdens[k] < right_burdens[k] for k in left_burdens
    )
    return weak and strict


def pareto_front(measurements: Iterable[StageMeasurement]) -> tuple[str, ...]:
    rows = tuple(measurements)
    if len({row.stage for row in rows}) != len(rows):
        raise ValueError("stage names must be unique within one benchmark case")
    return tuple(
        row.stage
        for row in rows
        if not any(other.stage != row.stage and dominates(other, row) for other in rows)
    )


def axis_delta(full: StageMeasurement, ablated: StageMeasurement) -> dict[str, float]:
    """Positive benefit deltas and negative burden deltas both favor the full layer."""

    delta = {k: full.benefit_axes()[k] - ablated.benefit_axes()[k] for k in full.benefit_axes()}
    delta.update({k: ablated.burden_axes()[k] - full.burden_axes()[k] for k in full.burden_axes()})
    return delta


def necessity_verdict(layer: str, full: StageMeasurement, ablated: StageMeasurement) -> dict[str, Any]:
    if dominates(full, ablated):
        verdict = "KEEP"
        reason = "full layer strictly Pareto-dominates its ablation"
    elif dominates(ablated, full):
        verdict = "GO_MIN"
        reason = "ablation strictly Pareto-dominates the full layer"
    else:
        verdict = "HOLD"
        reason = "trade-off remains; collect more evidence or declare a task-specific preference"
    return {
        "layer": layer,
        "full_stage": full.stage,
        "ablated_stage": ablated.stage,
        "verdict": verdict,
        "reason": reason,
        "axis_delta": axis_delta(full, ablated),
    }


def benchmark_report(
    measurements: Iterable[StageMeasurement],
    *,
    case_id: str,
    ablation_chain: Iterable[tuple[str, str, str]] = ABLATION_CHAIN,
) -> dict[str, Any]:
    rows = tuple(measurements)
    by_stage = {row.stage: row for row in rows}
    missing = [stage for stage in STAGE_ORDER if stage not in by_stage]
    if missing:
        raise ValueError(f"missing required benchmark stages: {missing}")

    necessity: list[dict[str, Any]] = []
    for layer, full_stage, ablated_stage in ablation_chain:
        if full_stage not in by_stage or ablated_stage not in by_stage:
            raise ValueError(f"ablation references unknown stages: {full_stage}, {ablated_stage}")
        necessity.append(necessity_verdict(layer, by_stage[full_stage], by_stage[ablated_stage]))

    report: dict[str, Any] = {
        "schema": "omega-ttm-bench/v1",
        "case_id": case_id,
        "stage_order": list(STAGE_ORDER),
        "measurements": [row.to_dict() for row in rows],
        "pareto_front": list(pareto_front(rows)),
        "necessity": necessity,
        "go_min_candidates": [item["layer"] for item in necessity if item["verdict"] == "GO_MIN"],
        "hold_layers": [item["layer"] for item in necessity if item["verdict"] == "HOLD"],
        "boundary": (
            "TTMBench performs Pareto and ablation analysis over supplied measurements. "
            "It does not manufacture task success, scientific truth, or universal utility weights."
        ),
    }
    report["fingerprint"] = stable_digest(report)
    return report
