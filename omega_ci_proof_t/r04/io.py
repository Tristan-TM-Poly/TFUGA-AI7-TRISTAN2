from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def read_json(path: str | Path) -> Mapping[str, Any]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise TypeError("JSON document must be an object")
    return raw


def write_json(path: str | Path, payload: Mapping[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
