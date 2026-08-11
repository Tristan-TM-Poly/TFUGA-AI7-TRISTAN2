from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Iterable


def _get(record: Any, key: str, default: Any = None) -> Any:
    if isinstance(record, dict):
        return record.get(key, default)
    return getattr(record, key, default)


def benchmark_to_eval_cases(record: Any) -> list[dict[str, Any]]:
    bid = str(_get(record, "id", "benchmark"))
    gid = str(_get(record, "generator_id", "generator"))
    variant = int(_get(record, "variant", 0))
    parameters = dict(_get(record, "parameters", {}) or {})
    expected = dict(_get(record, "expected", {}) or {})
    negative_control = str(_get(record, "negative_control", "negative_control"))
    oak_status = str(_get(record, "oak_status", "unknown"))

    positive = {
        "id": f"benchmark::{bid}",
        "prompt": (
            f"Evaluate generator {gid} benchmark {bid} variant {variant} with parameters "
            f"{json.dumps(parameters, sort_keys=True)}. Require expected contract "
            f"{json.dumps(expected, sort_keys=True)} and preserve OAK label {oak_status}."
        ),
        "class": "positive",
        "eval_dimension": "generator_benchmark",
        "benchmark_id": bid,
        "generator_id": gid,
        "expected": expected,
        "oak_status": oak_status,
    }
    control = {
        "id": f"benchmark-control::{bid}",
        "prompt": (
            f"Run the declared negative control `{negative_control}` for generator {gid} / benchmark {bid}; "
            "do not count the control as a benchmark pass and preserve the benchmark OAK label."
        ),
        "class": "edge",
        "eval_dimension": "generator_negative_control",
        "benchmark_id": bid,
        "generator_id": gid,
        "negative_control": negative_control,
        "oak_status": oak_status,
    }
    return [positive, control]


def enrich_spec_with_benchmarks(spec: dict[str, Any], records: Iterable[Any]) -> dict[str, Any]:
    out = copy.deepcopy(spec)
    gid = out.get("generator_discovery_provenance", {}).get("id")
    contracts = []
    cases = list(out.get("eval_cases", []))
    for record in records:
        record_gid = str(_get(record, "generator_id", ""))
        if gid and record_gid != gid:
            continue
        bid = str(_get(record, "id", "benchmark"))
        contracts.append({
            "benchmark_id": bid,
            "generator_id": record_gid,
            "variant": int(_get(record, "variant", 0)),
            "parameters": dict(_get(record, "parameters", {}) or {}),
            "expected": dict(_get(record, "expected", {}) or {}),
            "negative_control": str(_get(record, "negative_control", "")),
            "oak_status": str(_get(record, "oak_status", "unknown")),
        })
        cases.extend(benchmark_to_eval_cases(record))
    out["benchmark_contracts"] = contracts
    out["eval_cases"] = cases
    out.setdefault("invariants", []).append(
        "Generator benchmark templates and their OAK labels must not be upgraded into empirical evidence."
    )
    return out


def read_benchmark_jsonl(path: str | Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
