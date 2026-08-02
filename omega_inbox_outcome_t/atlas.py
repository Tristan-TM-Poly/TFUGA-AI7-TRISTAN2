"""Generate and audit the deterministic Ω-INBOX-TO-OUTCOME policy atlas."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterator, Sequence

INTENTS = tuple(f"intent_{i:02d}" for i in range(16))
DELIVERABLES = tuple(f"deliverable_{i:02d}" for i in range(12))
RISKS = tuple(f"risk_{i:02d}" for i in range(8))
AUTONOMY = tuple(f"L{i}" for i in range(6))
CHANNELS = ("email", "github", "drive", "portal")
LAYERS = ("plan", "gate", "evidence")
EXPECTED_CELLS = len(INTENTS) * len(DELIVERABLES) * len(RISKS) * len(AUTONOMY) * len(CHANNELS) * len(LAYERS)
EXPECTED_SHARDS = len(LAYERS) * len(INTENTS) * len(DELIVERABLES)


def cell_lines() -> Iterator[str]:
    for risk in RISKS:
        for autonomy in AUTONOMY:
            for channel in CHANNELS:
                yield f"{risk}|{autonomy}|{channel}"


def generate(root: Path) -> dict[str, int | str]:
    content = "\n".join(cell_lines()) + "\n"
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    for layer in LAYERS:
        for intent in INTENTS:
            for deliverable in DELIVERABLES:
                path = root / layer / intent / f"{deliverable}.cells"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
    manifest = {"cells": EXPECTED_CELLS, "shards": EXPECTED_SHARDS, "lines_per_shard": len(RISKS) * len(AUTONOMY) * len(CHANNELS), "shared_content_sha256": content_hash}
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def audit(root: Path) -> dict[str, int | bool]:
    expected = list(cell_lines())
    shards = 0
    cells = 0
    malformed = 0
    missing = 0
    for layer in LAYERS:
        for intent in INTENTS:
            for deliverable in DELIVERABLES:
                path = root / layer / intent / f"{deliverable}.cells"
                if not path.exists():
                    missing += 1
                    continue
                lines = path.read_text(encoding="utf-8").splitlines()
                shards += 1
                cells += len(lines)
                if lines != expected:
                    malformed += 1
    return {"passed": missing == 0 and malformed == 0 and shards == EXPECTED_SHARDS and cells == EXPECTED_CELLS, "shards": shards, "cells": cells, "missing": missing, "malformed": malformed}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-inbox-atlas")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("generate", "audit"):
        item = sub.add_parser(name)
        item.add_argument("root", type=Path)
    args = parser.parse_args(argv)
    result = generate(args.root) if args.command == "generate" else audit(args.root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("passed", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
