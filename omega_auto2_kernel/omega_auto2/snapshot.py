from __future__ import annotations

import json
from pathlib import Path

from .regression import current_canonical_suite


def canonical_snapshot(version: str = "0.8.0") -> dict[str, object]:
    suite = current_canonical_suite()
    return {
        "version": version,
        "kind": "canonical_benchmark_snapshot",
        "suite": suite,
    }


def snapshot_json(version: str = "0.8.0") -> str:
    return json.dumps(canonical_snapshot(version), ensure_ascii=False, indent=2, sort_keys=True)


def load_snapshot(path: str | Path) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
