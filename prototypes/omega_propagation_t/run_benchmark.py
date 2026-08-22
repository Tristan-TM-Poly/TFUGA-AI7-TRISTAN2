from __future__ import annotations

import json
from pathlib import Path

from omega_propagation import Edge, PropagationGraph, meta_level_justified


def load_cases():
    path = Path(__file__).parent / "benchmarks" / "cases.json"
    return json.loads(path.read_text(encoding="utf-8"))


def run():
    cases = load_cases()
    results = []
    for case in cases["route_cases"]:
        graph = PropagationGraph([Edge(**edge) for edge in case["edges"]])
        receipt = graph.best_route(
            case["source"],
            case["target"],
            amount=case.get("amount", 1.0),
            **case.get("weights", {}),
        )
        passed = list(receipt.path) == case["expected_path"]
        results.append(
            {
                "id": case["id"],
                "passed": passed,
                "path": list(receipt.path),
                "expected_path": case["expected_path"],
                "score": receipt.score,
                "fidelity": receipt.fidelity,
                "risk": receipt.cumulative_risk,
            }
        )

    meta = cases["meta_level_case"]
    meta_pass = meta_level_justified(**meta["inputs"]) == meta["expected_justified"]
    results.append({"id": meta["id"], "passed": meta_pass})

    summary = {
        "status": "PASS" if all(r["passed"] for r in results) else "FAIL",
        "passed": sum(1 for r in results if r["passed"]),
        "total": len(results),
        "results": results,
        "oak_note": "Benchmark PASS means only the specified toy claims passed; it is not proof of a universal propagation theory.",
    }
    print(json.dumps(summary, indent=2))
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(run())
