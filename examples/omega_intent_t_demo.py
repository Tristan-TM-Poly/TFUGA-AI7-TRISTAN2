from __future__ import annotations

import json
from pathlib import Path
import tempfile

from omega_intent_t import Intent, IntentCompiler, LogicalFrontier


intent = Intent.from_mapping({
    "objective": (
        "Develop Tristan fractal transforms, compare them with classical baselines, "
        "produce Python, Rust and C++ packages, tests, benchmarks, reports and product hypotheses."
    ),
    "expected_outputs": [
        "theory_documents",
        "mathematical_specifications",
        "code",
        "tests",
        "benchmarks",
        "reports",
        "product_analysis",
        "ip_analysis",
    ],
    "languages": ["python", "rust", "cpp"],
    "mode": "frontier",
})

with tempfile.TemporaryDirectory(prefix="omega-intent-demo-") as directory:
    result = IntentCompiler().compile(
        intent,
        Path(directory) / "bundle",
        materialize_scaffolds=True,
        github_plan=True,
    )
    payload = {
        "compilation": result.to_dict(),
        "frontier": LogicalFrontier().manifest(),
        "oak": result.oak_report.to_dict(),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
