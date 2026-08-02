"""Deterministic CVCD-style policy atlas for mail-to-GitHub loops."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Sequence

INTENTS = (
    "improve", "fix_bug", "add_tests", "document", "benchmark", "secure", "refactor", "package",
    "research_to_prototype", "ci_repair", "dependency_update", "performance", "accessibility", "localize",
    "productize", "mminus_regression",
)
TARGETS = (
    "python_module", "cli", "api", "workflow", "documentation", "tests", "schema", "dataset",
    "notebook", "frontend", "backend", "security_policy", "packaging", "release_candidate", "benchmark", "repository",
)
RISKS = ("none", "scope", "security", "privacy", "ip", "dependency", "ci", "regression")
AUTHORITIES = ("read", "issue", "branch", "commit", "draft_pr", "review_ready")
ACTIONS = ("plan", "mutate", "validate", "report")
LAYERS = ("plan", "gate", "evidence")
EXPECTED_SHARDS = len(LAYERS) * len(INTENTS) * len(TARGETS)
CELLS_PER_SHARD = len(RISKS) * len(AUTHORITIES) * len(ACTIONS)
EXPECTED_CELLS = EXPECTED_SHARDS * CELLS_PER_SHARD


def _lines() -> list[str]:
    return [f"r{ri:02d}|u{ui:02d}|a{ai:02d}" for ri in range(len(RISKS)) for ui in range(len(AUTHORITIES)) for ai in range(len(ACTIONS))]


def generate(root: Path) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    content = "\n".join(_lines()) + "\n"
    content_hash = sha256(content.encode("utf-8")).hexdigest()
    for layer in LAYERS:
        for ii in range(len(INTENTS)):
            directory = root / layer / f"i{ii:02d}"
            directory.mkdir(parents=True, exist_ok=True)
            for ti in range(len(TARGETS)):
                (directory / f"t{ti:02d}.cells").write_text(content, encoding="utf-8")
    manifest = {
        "schema": "omega-mail-github-loop-atlas-r0.1",
        "intents": len(INTENTS), "targets": len(TARGETS), "risks": len(RISKS),
        "authorities": len(AUTHORITIES), "actions": len(ACTIONS), "layers": len(LAYERS),
        "shards": EXPECTED_SHARDS, "cells_per_shard": CELLS_PER_SHARD, "cells": EXPECTED_CELLS,
        "content_sha256": content_hash, "external_mutation": False, "merge_allowed": False, "release_allowed": False,
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def audit(root: Path) -> dict:
    expected_lines = _lines()
    missing = malformed = observed_cells = 0
    hashes: set[str] = set()
    for layer in LAYERS:
        for ii in range(len(INTENTS)):
            for ti in range(len(TARGETS)):
                path = root / layer / f"i{ii:02d}" / f"t{ti:02d}.cells"
                if not path.exists():
                    missing += 1
                    continue
                raw = path.read_text(encoding="utf-8")
                lines = raw.splitlines()
                if lines != expected_lines:
                    malformed += 1
                observed_cells += len(lines)
                hashes.add(sha256(raw.encode("utf-8")).hexdigest())
    return {
        "passed": missing == 0 and malformed == 0 and observed_cells == EXPECTED_CELLS and len(hashes) == 1,
        "missing": missing, "malformed": malformed, "observed_cells": observed_cells,
        "expected_cells": EXPECTED_CELLS, "unique_shard_hashes": len(hashes),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-mail-github-atlas")
    sub = parser.add_subparsers(dest="command", required=True)
    gen = sub.add_parser("generate"); gen.add_argument("root", type=Path)
    aud = sub.add_parser("audit"); aud.add_argument("root", type=Path)
    args = parser.parse_args(argv)
    result = generate(args.root) if args.command == "generate" else audit(args.root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if args.command == "generate" or result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
