from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .delta import write_delta
from .export import write_graph_exports
from .index import append_snapshot, verify_index, write_longitudinal_reports
from .render import render_markdown, write_bundle, write_operational_views
from .summarizer import AUDIENCES, SummaryEngine


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-summary",
        description="Ω-SUMMARY-FRACTAL-T∞ deterministic multi-depth repository summarizer",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate")
    generate.add_argument("root", nargs="?", default=".")
    generate.add_argument("--depth", type=int, default=3)
    generate.add_argument("--audience", choices=sorted(AUDIENCES), default="tristan")
    generate.add_argument("--focus")
    generate.add_argument("--output-dir")
    generate.add_argument("--json", action="store_true", dest="json_stdout")
    generate.add_argument("--max-files", type=int, default=20000)

    all_depths = subparsers.add_parser("all-depths")
    all_depths.add_argument("root", nargs="?", default=".")
    all_depths.add_argument("--audience", choices=sorted(AUDIENCES), default="tristan")
    all_depths.add_argument("--focus")
    all_depths.add_argument("--output-dir", default=".omega/summary")
    all_depths.add_argument("--max-files", type=int, default=20000)

    audit = subparsers.add_parser("audit")
    audit.add_argument("root", nargs="?", default=".")
    audit.add_argument("--max-files", type=int, default=20000)
    audit.add_argument("--fail-on-gap", action="store_true")

    delta = subparsers.add_parser("delta")
    delta.add_argument("previous", help="previous summary_dN_<audience>.json")
    delta.add_argument("current", help="current summary_dN_<audience>.json")
    delta.add_argument("--output-dir", default=".omega/summary-delta")

    index = subparsers.add_parser("index")
    index.add_argument("summary", help="repository or corpus summary JSON snapshot")
    index.add_argument("--index-file", default=".omega/corpus-index.json")
    index.add_argument("--report-dir", default=".omega/longitudinal")

    export = subparsers.add_parser("export")
    export.add_argument("summary", help="repository summary JSON snapshot")
    export.add_argument("--output-dir", default=".omega/graph-export")

    return parser


def cmd_generate(args: argparse.Namespace) -> int:
    bundle = SummaryEngine(args.root, max_files=args.max_files).generate(
        depth=args.depth,
        audience=args.audience,
        focus=args.focus,
    )
    if args.output_dir:
        paths = write_bundle(bundle, args.output_dir)
        if args.depth >= 3:
            paths.update(write_operational_views(bundle, args.output_dir))
        print(json.dumps({key: str(value) for key, value in paths.items()}, sort_keys=True))
    elif args.json_stdout:
        print(json.dumps(bundle.to_dict(), indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(render_markdown(bundle))
    return 0


def cmd_all_depths(args: argparse.Namespace) -> int:
    engine = SummaryEngine(args.root, max_files=args.max_files)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    index = []
    for depth in range(10):
        bundle = engine.generate(depth=depth, audience=args.audience, focus=args.focus)
        paths = write_bundle(bundle, out)
        index.append(
            {
                "depth": depth,
                "fingerprint": bundle.cache_fingerprint,
                "markdown": str(paths["markdown"]),
                "json": str(paths["json"]),
            }
        )
        if depth == 9:
            write_operational_views(bundle, out)
    (out / "depth_index.json").write_text(
        json.dumps(index, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"generated_depths": 10, "output_dir": str(out)}, sort_keys=True))
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    bundle = SummaryEngine(args.root, max_files=args.max_files).generate(depth=8, audience="oak")
    payload = {
        "valid": not bool(bundle.gaps),
        "gap_count": len(bundle.gaps),
        "health": bundle.health,
        "duplicate_candidates": bundle.duplicate_candidates,
        "fingerprint": bundle.cache_fingerprint,
    }
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    return 2 if args.fail_on_gap and bundle.gaps else 0


def cmd_delta(args: argparse.Namespace) -> int:
    paths = write_delta(args.previous, args.current, args.output_dir)
    print(json.dumps({key: str(value) for key, value in paths.items()}, sort_keys=True))
    return 0


def cmd_index(args: argparse.Namespace) -> int:
    index = append_snapshot(args.index_file, args.summary)
    paths = write_longitudinal_reports(args.index_file, args.report_dir)
    print(
        json.dumps(
            {
                "index_file": str(args.index_file),
                "run_count": len(index.get("runs", [])),
                "valid_hash_chain": verify_index(index),
                **{key: str(value) for key, value in paths.items()},
            },
            sort_keys=True,
        )
    )
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    paths = write_graph_exports(args.summary, args.output_dir)
    print(json.dumps({key: str(value) for key, value in paths.items()}, sort_keys=True))
    return 0


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "generate":
        return cmd_generate(args)
    if args.command == "all-depths":
        return cmd_all_depths(args)
    if args.command == "audit":
        return cmd_audit(args)
    if args.command == "delta":
        return cmd_delta(args)
    if args.command == "index":
        return cmd_index(args)
    if args.command == "export":
        return cmd_export(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
