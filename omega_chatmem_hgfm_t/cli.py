from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import diff_manifests, recall, run_pipeline


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="omega-chatmem",
        description="Ω-CHATMEM-HGFM-T∞ — compile ChatGPT exports into an OAK-safe HGFM memory.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    for name in ("ingest", "sync"):
        s = sub.add_parser(name, help="Ingest a ChatGPT export and rebuild derived HGFM artifacts.")
        s.add_argument("input", help="Path to conversations.json or compatible JSON.")
        s.add_argument("output", help="Output directory for derived public-safe memory artifacts.")

    r = sub.add_parser("recall", help="Retrieve a compact relevant subgraph.")
    r.add_argument("output", help="Existing generated memory directory.")
    r.add_argument("query", help="Topic/system/query to recall.")
    r.add_argument("--limit", type=int, default=24)

    c = sub.add_parser("capsule", help="Print the generated MEMORY_CAPSULE.md.")
    c.add_argument("output")

    o = sub.add_parser("oak", help="Print the structural OAK report.")
    o.add_argument("output")

    d = sub.add_parser("diff", help="Compare two generated manifests.")
    d.add_argument("old_manifest")
    d.add_argument("new_manifest")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    if args.command in {"ingest", "sync"}:
        result = run_pipeline(args.input, args.output)
        print(json.dumps(result.__dict__, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if args.command == "recall":
        print(json.dumps(recall(args.output, args.query, args.limit), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if args.command == "capsule":
        print((Path(args.output) / "canon" / "MEMORY_CAPSULE.md").read_text(encoding="utf-8"))
        return 0

    if args.command == "oak":
        print((Path(args.output) / "reports" / "oak_report.json").read_text(encoding="utf-8"))
        return 0

    if args.command == "diff":
        print(json.dumps(diff_manifests(args.old_manifest, args.new_manifest), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
