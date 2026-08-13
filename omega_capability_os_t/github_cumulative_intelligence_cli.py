from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .github_cumulative_intelligence import CumulativeIntelligenceCompiler
from .github_memory import CapabilityRequest, GitHubMemoryIndex


def _load(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path: str | None, payload: dict[str, Any]) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-github-cumulative-intelligence")
    parser.add_argument("request", help="CapabilityRequest JSON")
    parser.add_argument(
        "--index",
        action="append",
        required=True,
        metavar="REPOSITORY=PATH",
        help="Repeatable canonical #447 memory index, e.g. owner/repo=/tmp/index.json",
    )
    parser.add_argument("--max-items", type=int, default=8)
    parser.add_argument("--output")
    args = parser.parse_args(argv)

    indexes: dict[str, GitHubMemoryIndex] = {}
    for item in args.index:
        if "=" not in item:
            raise SystemExit("--index requires REPOSITORY=PATH")
        repository, path = item.split("=", 1)
        repository = repository.strip()
        if not repository:
            raise SystemExit("--index repository cannot be empty")
        indexes[repository] = GitHubMemoryIndex.from_dict(_load(path))

    request = CapabilityRequest.from_dict(_load(args.request))
    payload = CumulativeIntelligenceCompiler().compile(
        indexes,
        request,
        max_items=max(1, args.max_items),
    )
    _write(args.output, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
