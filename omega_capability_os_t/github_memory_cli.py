from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .github_memory import CapabilityRequest, GitHubMemoryIndex, ReuseBeforeCreateGate, build_live_index


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path: str | None, payload: dict) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-github-memory")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="Build a fresh read-only PR memory index from GitHub")
    build.add_argument("--repository", required=True)
    build.add_argument("--registry", help="Optional Capability OS registry JSON")
    build.add_argument("--output")
    build.add_argument("--token-env", default="GITHUB_TOKEN")
    build.add_argument("--without-files", action="store_true")
    build.add_argument("--max-prs", type=int)

    check = sub.add_parser("reuse-check", help="Run ReuseBeforeCreateGate")
    check.add_argument("index")
    check.add_argument("request")
    check.add_argument("--output")

    context = sub.add_parser("context", help="Compile a bounded LLMT context packet")
    context.add_argument("index")
    context.add_argument("request")
    context.add_argument("--max-items", type=int, default=8)
    context.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "build":
        registry = _load(args.registry) if args.registry else None
        token = os.getenv(args.token_env) if args.token_env else None
        index = build_live_index(
            args.repository,
            token=token,
            capability_registry=registry,
            include_files=not args.without_files,
            max_prs=args.max_prs,
        )
        payload = index.to_dict()
        _write(args.output, payload)
        return 0

    index = GitHubMemoryIndex.from_dict(_load(args.index))
    request = CapabilityRequest.from_dict(_load(args.request))
    gate = ReuseBeforeCreateGate(index)
    if args.command == "reuse-check":
        payload = gate.decide(request).to_dict()
    else:
        payload = gate.compile_context(request, max_items=args.max_items)
    _write(args.output, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
