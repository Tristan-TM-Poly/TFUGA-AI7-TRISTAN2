"""Historical test sharding and early-failure ordering for Ω-ACTIONS-T∞."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Iterable


def _records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("tests", "observations", "records"):
            value = payload.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
    return []


def normalize_tests(payload: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in _records(payload):
        nodeid = str(raw.get("nodeid") or raw.get("test") or raw.get("name") or "").strip()
        if not nodeid:
            continue
        duration = max(float(raw.get("duration_seconds") or raw.get("duration") or 0.0), 0.001)
        runs = max(int(raw.get("runs") or raw.get("count") or 0), 0)
        failures = max(int(raw.get("failures") or raw.get("failure_count") or 0), 0)
        failures = min(failures, runs) if runs else failures
        alpha = 1.0 + failures
        beta = 1.0 + max(runs - failures, 0)
        posterior_fail = alpha / (alpha + beta)
        rows.append({
            "nodeid": nodeid,
            "duration_seconds": round(duration, 6),
            "runs": runs,
            "failures": failures,
            "posterior_failure_probability": round(posterior_fail, 6),
            "early_failure_value": round(posterior_fail / duration, 6),
        })
    return rows


def choose_shard_count(
    tests: list[dict[str, Any]],
    *,
    shards: int | None = None,
    target_seconds: float | None = None,
    capacity: int | None = None,
) -> int:
    if not tests:
        return 0
    if shards is not None:
        count = max(int(shards), 1)
    elif target_seconds is not None and target_seconds > 0:
        total = sum(float(row["duration_seconds"]) for row in tests)
        count = max(1, math.ceil(total / target_seconds))
    else:
        count = 1
    count = min(count, len(tests))
    if capacity is not None and capacity > 0:
        count = min(count, int(capacity))
    return max(count, 1)


def shard_tests(
    payload: Any,
    *,
    shards: int | None = None,
    target_seconds: float | None = None,
    capacity: int | None = None,
) -> dict[str, Any]:
    tests = normalize_tests(payload)
    count = choose_shard_count(tests, shards=shards, target_seconds=target_seconds, capacity=capacity)
    if count == 0:
        return {
            "schema": "omega-actions-sharding/v0.4",
            "aggregate": {"test_count": 0, "shard_count": 0, "estimated_total_seconds": 0.0},
            "shards": [],
            "matrix": {"include": []},
            "oak_limits": ["No tests were provided."],
        }

    bins = [{"shard": i + 1, "estimated_seconds": 0.0, "tests": []} for i in range(count)]
    for test in sorted(tests, key=lambda row: (-float(row["duration_seconds"]), row["nodeid"])):
        target = min(bins, key=lambda row: (float(row["estimated_seconds"]), row["shard"]))
        target["tests"].append(test)
        target["estimated_seconds"] = round(float(target["estimated_seconds"]) + float(test["duration_seconds"]), 6)

    for bucket in bins:
        bucket["tests"].sort(key=lambda row: (-float(row["early_failure_value"]), row["nodeid"]))
        bucket["nodeids"] = [row["nodeid"] for row in bucket["tests"]]

    loads = [float(bucket["estimated_seconds"]) for bucket in bins]
    total = sum(loads)
    mean = total / len(loads)
    maximum = max(loads)
    matrix = {
        "include": [
            {"shard": bucket["shard"], "estimated_seconds": bucket["estimated_seconds"], "test_count": len(bucket["tests"])}
            for bucket in bins
        ]
    }
    return {
        "schema": "omega-actions-sharding/v0.4",
        "aggregate": {
            "test_count": len(tests),
            "shard_count": count,
            "estimated_total_seconds": round(total, 6),
            "estimated_parallel_wall_seconds": round(maximum, 6),
            "mean_shard_seconds": round(mean, 6),
            "imbalance_ratio": round(maximum / mean, 6) if mean else 1.0,
        },
        "shards": bins,
        "matrix": matrix,
        "policy": {
            "algorithm": "LPT-duration-balance + Beta(1,1) early-failure ordering",
            "target_seconds": target_seconds,
            "capacity": capacity,
            "explicit_shards": shards,
        },
        "oak_limits": [
            "Historical duration predicts scheduling cost but can drift with code, hardware and environment.",
            "Beta-Bernoulli failure probability is a ranking model, not proof that a test will fail.",
            "Capacity is an external runner/budget constraint; the engine does not invent a universal max-parallel ceiling.",
            "Exhaustive coverage is preserved: sharding changes placement/order, not which tests exist.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    a = report["aggregate"]
    lines = [
        "# Ω-ACTIONS-T∞ — Historical Test Sharding", "",
        f"- Tests: **{a['test_count']}**", f"- Shards: **{a['shard_count']}**",
        f"- Estimated total work: **{a['estimated_total_seconds']} s**",
        f"- Estimated parallel wall: **{a.get('estimated_parallel_wall_seconds', 0)} s**",
        f"- Imbalance ratio: **{a.get('imbalance_ratio', 1.0)}**", "", "## Shards", "",
    ]
    for bucket in report["shards"]:
        lines.append(f"- shard {bucket['shard']}: {len(bucket['tests'])} tests, {bucket['estimated_seconds']} s")
    lines += ["", "## OAK limits", ""]
    lines.extend(f"- {item}" for item in report["oak_limits"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-actions-shard", description="Balance tests from historical durations.")
    parser.add_argument("input", help="JSON test history")
    parser.add_argument("--shards", type=int)
    parser.add_argument("--target-seconds", type=float)
    parser.add_argument("--capacity", type=int)
    parser.add_argument("--json-out")
    parser.add_argument("--markdown-out")
    parser.add_argument("--format", choices=("summary", "json", "markdown"), default="summary")
    args = parser.parse_args(argv)
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    report = shard_tests(payload, shards=args.shards, target_seconds=args.target_seconds, capacity=args.capacity)
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.markdown_out:
        Path(args.markdown_out).write_text(render_markdown(report), encoding="utf-8")
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    elif args.format == "markdown":
        print(render_markdown(report), end="")
    else:
        a = report["aggregate"]
        print(f"Ω-ACTIONS-T∞ sharding tests={a['test_count']} shards={a['shard_count']} parallel_wall={a.get('estimated_parallel_wall_seconds', 0)}s imbalance={a.get('imbalance_ratio', 1.0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
