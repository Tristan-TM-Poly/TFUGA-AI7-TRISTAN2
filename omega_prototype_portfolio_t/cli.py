"""CLI for Ω-PROTOTYPE-PORTFOLIO-T∞."""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from .core import analyze, audit, compare, compile_bundle, graphml, load_snapshot, plan
from .grand_atlas import compile_grand_atlas, grand_atlas_report, memory_markdown
from .seed import seed_snapshot


def _write_or_print(payload: object, output: str | None, pretty: bool = True) -> None:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2 if pretty else None) + "\n"
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-prototype-portfolio")
    sub = parser.add_subparsers(dest="command", required=True)
    seed = sub.add_parser("seed", help="emit the dated canonical seed")
    seed.add_argument("--output")
    for name in ("audit", "analyze", "graph"):
        cmd = sub.add_parser(name)
        cmd.add_argument("snapshot", nargs="?")
        cmd.add_argument("--output")
    planner = sub.add_parser("plan")
    planner.add_argument("snapshot", nargs="?")
    planner.add_argument("--output")
    planner.add_argument("--max-items", type=int, default=6)
    planner.add_argument("--max-hours", type=int, default=40)
    compile_cmd = sub.add_parser("compile")
    compile_cmd.add_argument("snapshot", nargs="?")
    compile_cmd.add_argument("--output-dir", required=True)
    compile_cmd.add_argument("--max-items", type=int, default=6)
    compile_cmd.add_argument("--max-hours", type=int, default=40)
    atlas = sub.add_parser("grand-atlas")
    atlas.add_argument("snapshot", nargs="?")
    atlas.add_argument("--output")
    atlas.add_argument("--output-dir")
    memory = sub.add_parser("memory")
    memory.add_argument("snapshot", nargs="?")
    memory.add_argument("--output")
    delta = sub.add_parser("compare")
    delta.add_argument("left")
    delta.add_argument("right")
    delta.add_argument("--output")
    oak = sub.add_parser("oak")
    oak.add_argument("--output")
    return parser


def _snapshot(path: str | None):
    return load_snapshot(path) if path else seed_snapshot()


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "seed":
        _write_or_print(seed_snapshot().to_dict(), args.output)
        return 0
    if args.command == "audit":
        report = audit(_snapshot(args.snapshot))
        _write_or_print(report, args.output)
        return 0 if report["status"] == "PASS" else 2
    if args.command == "analyze":
        _write_or_print(analyze(_snapshot(args.snapshot)), args.output)
        return 0
    if args.command == "plan":
        _write_or_print(plan(_snapshot(args.snapshot), max_items=args.max_items, max_hours=args.max_hours), args.output)
        return 0
    if args.command == "graph":
        text = graphml(_snapshot(args.snapshot))
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        return 0
    if args.command == "compile":
        receipts = compile_bundle(_snapshot(args.snapshot), args.output_dir, max_items=args.max_items, max_hours=args.max_hours)
        _write_or_print(receipts, None)
        return 0
    if args.command == "grand-atlas":
        snapshot = _snapshot(args.snapshot)
        if args.output_dir:
            _write_or_print(compile_grand_atlas(snapshot, args.output_dir), args.output)
        else:
            _write_or_print(grand_atlas_report(snapshot), args.output)
        return 0
    if args.command == "memory":
        text = memory_markdown(_snapshot(args.snapshot))
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        return 0
    if args.command == "compare":
        _write_or_print(compare(load_snapshot(args.left), load_snapshot(args.right)), args.output)
        return 0
    if args.command == "oak":
        snapshot = seed_snapshot()
        analysis = analyze(snapshot)
        portfolio_plan = plan(snapshot)
        report = audit(snapshot)
        atlas = grand_atlas_report(snapshot)
        with (
            tempfile.TemporaryDirectory() as one,
            tempfile.TemporaryDirectory() as two,
            tempfile.TemporaryDirectory() as atlas_one,
            tempfile.TemporaryDirectory() as atlas_two,
        ):
            r1 = compile_bundle(snapshot, one)
            r2 = compile_bundle(snapshot, two)
            deterministic = r1 == r2 and all(
                (Path(one) / name).read_bytes() == (Path(two) / name).read_bytes()
                for name in r1
            )
            g1 = compile_grand_atlas(snapshot, atlas_one)
            g2 = compile_grand_atlas(snapshot, atlas_two)
            grand_atlas_deterministic = g1 == g2 and all(
                (Path(atlas_one) / name).read_bytes() == (Path(atlas_two) / name).read_bytes()
                for name in g1
            )
        payload = {
            "status": "PASS" if report["status"] == "PASS" and deterministic and grand_atlas_deterministic else "FAIL",
            "prototype_count": len(snapshot.prototypes),
            "family_count": atlas["family_count"],
            "artifact_type_count": atlas["artifact_type_count"],
            "assessment_count": len(analysis["assessments"]),
            "m_minus_count": len(analysis["m_minus"]),
            "selected_count": portfolio_plan["selected_count"],
            "bundle_deterministic": deterministic,
            "grand_atlas_deterministic": grand_atlas_deterministic,
            "audit_status": report["status"],
            "snapshot_sha256": snapshot.sha256,
            "analysis_sha256": analysis["analysis_sha256"],
            "plan_sha256": portfolio_plan["plan_sha256"],
            "atlas_sha256": atlas["atlas_sha256"],
            "exhaustiveness_claimed": False,
            "external_action_performed": False,
            "truth_probability_claimed": False,
        }
        _write_or_print(payload, args.output)
        return 0 if payload["status"] == "PASS" else 2
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
