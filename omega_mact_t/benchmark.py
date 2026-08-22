from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .kernel import MactCompiler
from .models import EpistemicType, EvidenceRef, ResourceVector, TransformationCandidate, VerificationContract


@dataclass(frozen=True)
class BenchResult:
    case: str
    baseline_id: str
    selected_id: str
    baseline_cost: float
    selected_cost: float
    verified_semantics_match: bool

    @property
    def cost_reduction(self) -> float:
        return self.baseline_cost - self.selected_cost

    @property
    def passed(self) -> bool:
        return self.verified_semantics_match and self.selected_cost <= self.baseline_cost


def _ev(scope: str):
    return [EvidenceRef(f"ev-{scope}", EpistemicType.MEASURED, scope, independent=True)]


def run_benchmark() -> List[BenchResult]:
    compiler = MactCompiler()
    results: List[BenchResult] = []

    scope = "reuse-vs-recompute"
    candidates = [TransformationCandidate("no-action-1", "NO_ACTION", "no-result", ResourceVector(), evidence=_ev(scope)), TransformationCandidate("wait-1", "WAIT", "no-result-yet", ResourceVector(time=1.0), evidence=_ev(scope)), TransformationCandidate("reuse-1", "REUSE", "verified-result", ResourceVector(compute=0.1, memory_persistent=0.1), evidence=_ev(scope), rollback="drop cache"), TransformationCandidate("recompute-1", "COMPUTE", "verified-result", ResourceVector(compute=4.0, time=1.0), evidence=_ev(scope), rollback="discard result")]
    selected = compiler.select(candidates, VerificationContract(required_scope=scope, required_semantic_effect="verified-result"))
    baseline = next(c for c in candidates if c.id == "recompute-1")
    selected_cost = selected.resources.weighted_cost(compiler.weights) if selected else float("inf")
    results.append(BenchResult(scope, baseline.id, selected.id if selected else "HOLD", baseline.resources.weighted_cost(compiler.weights), selected_cost, bool(selected and selected.semantic_effect == baseline.semantic_effect)))

    scope = "regenerate-vs-persist"
    candidates = [TransformationCandidate("no-action-2", "NO_ACTION", "no-artifact", ResourceVector(), evidence=_ev(scope)), TransformationCandidate("wait-2", "WAIT", "no-artifact-yet", ResourceVector(time=1.0), evidence=_ev(scope)), TransformationCandidate("reuse-2", "REUSE", "artifact", ResourceVector(compute=0.5, memory_persistent=0.2), evidence=_ev(scope), rollback="discard regenerated artifact", expected_future_work_avoided=2.0), TransformationCandidate("persist-2", "STORE", "artifact", ResourceVector(memory_persistent=3.0, persistent_complexity=0.5), evidence=_ev(scope), rollback="remove cache index")]
    selected = compiler.select(candidates, VerificationContract(required_scope=scope, required_semantic_effect="artifact"))
    baseline = next(c for c in candidates if c.id == "persist-2")
    selected_cost = selected.resources.weighted_cost(compiler.weights) if selected else float("inf")
    results.append(BenchResult(scope, baseline.id, selected.id if selected else "HOLD", baseline.resources.weighted_cost(compiler.weights), selected_cost, bool(selected and selected.semantic_effect == baseline.semantic_effect)))
    return results


def main() -> int:
    results = run_benchmark()
    for r in results:
        print(f"{r.case}: baseline={r.baseline_id} selected={r.selected_id} reduction={r.cost_reduction:.3f} pass={r.passed}")
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
