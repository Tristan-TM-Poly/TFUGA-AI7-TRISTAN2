"""Before/after OAK Promotion Gate for Ω-ACTIONS-T∞ R0.8."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _metric(report: dict[str, Any], group: str, name: str) -> float | None:
    value = ((report.get("aggregate") or {}).get(group) or {}).get(name)
    return float(value) if value is not None else None


def _relative_improvement(before: float | None, after: float | None) -> float | None:
    if before is None or after is None or before <= 0:
        return None
    return (before - after) / before


def compare_telemetry(
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    proof_gates: dict[str, bool | None] | None = None,
    min_completed_runs: int = 10,
    min_duration_p95_improvement: float = 0.05,
    max_failure_rate_increase: float = 0.02,
) -> dict[str, Any]:
    """Decide whether a CI optimization candidate has enough evidence to promote."""
    proof_gates = dict(proof_gates or {})
    required_gates = (
        "coverage_preserved",
        "required_checks_preserved",
        "permissions_non_escalating",
        "rollback_ready",
    )
    gate_state = {key: proof_gates.get(key) for key in required_gates}

    before_a = before.get("aggregate") or {}
    after_a = after.get("aggregate") or {}
    before_n = int(before_a.get("completed_runs") or 0)
    after_n = int(after_a.get("completed_runs") or 0)
    before_failure = before_a.get("failure_rate_completed")
    after_failure = after_a.get("failure_rate_completed")
    before_failure = float(before_failure) if before_failure is not None else None
    after_failure = float(after_failure) if after_failure is not None else None
    failure_delta = None
    if before_failure is not None and after_failure is not None:
        failure_delta = after_failure - before_failure

    before_duration_p95 = _metric(before, "duration_seconds", "p95")
    after_duration_p95 = _metric(after, "duration_seconds", "p95")
    before_queue_p95 = _metric(before, "queue_seconds", "p95")
    after_queue_p95 = _metric(after, "queue_seconds", "p95")
    duration_improvement = _relative_improvement(before_duration_p95, after_duration_p95)
    queue_improvement = _relative_improvement(before_queue_p95, after_queue_p95)

    blockers: list[str] = []
    warnings: list[str] = []
    if before_n < min_completed_runs or after_n < min_completed_runs:
        blockers.append("insufficient_completed_run_sample")
    unknown_gates = [key for key, value in gate_state.items() if value is None]
    failed_gates = [key for key, value in gate_state.items() if value is False]
    if unknown_gates:
        blockers.append("unknown_proof_gates")
    if failed_gates:
        blockers.append("failed_proof_gates")
    if failure_delta is None:
        blockers.append("missing_failure_rate")
    elif failure_delta > max_failure_rate_increase:
        blockers.append("failure_rate_regression")
    if duration_improvement is None:
        blockers.append("missing_duration_p95")
    elif duration_improvement < min_duration_p95_improvement:
        warnings.append("duration_gain_below_materiality_threshold")

    if "failed_proof_gates" in blockers or "failure_rate_regression" in blockers:
        decision = "REJECT_REGRESSION"
    elif blockers:
        decision = "INSUFFICIENT_EVIDENCE"
    elif warnings:
        decision = "HOLD_NO_MATERIAL_GAIN"
    else:
        decision = "PROMOTE_CANDIDATE"

    return {
        "schema": "omega-actions-promotion-gate/v0.8",
        "decision": decision,
        "thresholds": {
            "min_completed_runs": min_completed_runs,
            "min_duration_p95_improvement": min_duration_p95_improvement,
            "max_failure_rate_increase": max_failure_rate_increase,
        },
        "sample": {"before_completed_runs": before_n, "after_completed_runs": after_n},
        "before": {
            "duration_p95_seconds": before_duration_p95,
            "queue_p95_seconds": before_queue_p95,
            "failure_rate_completed": before_failure,
        },
        "after": {
            "duration_p95_seconds": after_duration_p95,
            "queue_p95_seconds": after_queue_p95,
            "failure_rate_completed": after_failure,
        },
        "deltas": {
            "duration_p95_relative_improvement": round(duration_improvement, 6) if duration_improvement is not None else None,
            "queue_p95_relative_improvement": round(queue_improvement, 6) if queue_improvement is not None else None,
            "failure_rate_delta": round(failure_delta, 6) if failure_delta is not None else None,
        },
        "proof_gates": gate_state,
        "unknown_proof_gates": unknown_gates,
        "failed_proof_gates": failed_gates,
        "blockers": blockers,
        "warnings": warnings,
        "automatic_merge_authorized": False,
        "oak_limits": [
            "Promotion compares observed samples but does not prove causal attribution.",
            "Comparable workload, runner class and repository conditions are required for a strong before/after claim.",
            "Passing this gate never authorizes automatic merge; repository governance remains separate.",
            "Coverage and required-check preservation are explicit gates rather than inferred from speed metrics.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-actions-promote", description="Evaluate before/after CI telemetry against OAK promotion gates.")
    parser.add_argument("before")
    parser.add_argument("after")
    parser.add_argument("--proof-gates", required=True, help="JSON object/file with coverage/required-check/permission/rollback booleans")
    parser.add_argument("--min-completed-runs", type=int, default=10)
    parser.add_argument("--min-duration-p95-improvement", type=float, default=0.05)
    parser.add_argument("--max-failure-rate-increase", type=float, default=0.02)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    before = json.loads(Path(args.before).read_text(encoding="utf-8"))
    after = json.loads(Path(args.after).read_text(encoding="utf-8"))
    proof_text = args.proof_gates
    proof_path = Path(proof_text)
    if proof_path.exists():
        proof = json.loads(proof_path.read_text(encoding="utf-8"))
    else:
        proof = json.loads(proof_text)
    report = compare_telemetry(
        before,
        after,
        proof_gates=proof,
        min_completed_runs=args.min_completed_runs,
        min_duration_p95_improvement=args.min_duration_p95_improvement,
        max_failure_rate_increase=args.max_failure_rate_increase,
    )
    Path(args.out).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Ω-ACTIONS-T∞ promotion decision={report['decision']} blockers={len(report['blockers'])} warnings={len(report['warnings'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
