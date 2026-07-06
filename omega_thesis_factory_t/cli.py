"""CLI for Ω-THESIS-2N-GIT-T."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import build_page_tree, example_seed, oak_report


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-thesis", description="Ω-THESIS-2N-GIT-T MVP CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    init_p = sub.add_parser("init", help="write an example ThesisSeed JSON")
    init_p.add_argument("--output", default="generated/omega_thesis/thesis_seed.json")

    expand_p = sub.add_parser("expand", help="expand the example seed into a 2^n LOG/EXP PageTree")
    expand_p.add_argument("--depth", type=int, default=3)
    expand_p.add_argument("--output", default="generated/omega_thesis/page_tree.json")

    oak_p = sub.add_parser("oak", help="write a compact OAK report for a PageTree expansion")
    oak_p.add_argument("--depth", type=int, default=3)
    oak_p.add_argument("--output", default="generated/omega_thesis/oak_report.json")

    args = parser.parse_args(argv)
    seed = example_seed()

    if args.command == "init":
        _write_json(Path(args.output), seed.to_dict())
        print(f"wrote {args.output}")
        return 0

    if args.command == "expand":
        nodes = build_page_tree(seed, depth=args.depth)
        _write_json(Path(args.output), [node.to_dict() for node in nodes])
        print(f"wrote {len(nodes)} nodes to {args.output}")
        return 0

    if args.command == "oak":
        nodes = build_page_tree(seed, depth=args.depth)
        report = oak_report(seed, nodes)
        _write_json(Path(args.output), report)
        print(f"wrote OAK report to {args.output}")
        return 0

    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
