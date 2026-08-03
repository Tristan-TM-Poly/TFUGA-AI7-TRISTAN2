"""CLI for Ω-PROTOTYPE-PORTFOLIO-T∞."""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from .core import analyze, audit, compare, compile_bundle, graphml, load_snapshot, plan
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
        report = audit(_snapshot(args.snapshot)); _write_or_print(report, args.output); return 0 if report["status"] == "PASS" else 2
    if args.command == "analyze":
        _write_or_print(analyze(_snapshot(args.snapshot)), args.output); return 0
    if args.command == "plan":
        _write_or_print(plan(_snapshot(args.snapshot), max_items=args.max_items, max_hours=args.max_hours), args.output); return 0
    if args.command == "graph":
        text = graphml(_snapshot(args.snapshot))
        if args.output: Path(args.output).write_text(text, encoding="utf-8")
        else: print(text, end="")
        return 0
    if args.command == "compile":
        receipts = compile_bundle(_snapshot(args.snapshot), args.output_dir, max_items=args.max_items, max_hours=args.max_hours); _write_or_print(receipts, None); return 0
    if args.command == "compare":
        _write_or_print(compare(load_snapshot(args.left), load_snapshot(args.right)), args.output); return 0
    if args.command == "oak":
        snapshot = seed_snapshot(); a = analyze(snapshot); p = plan(snapshot); report = audit(snapshot)
        with tempfile.TemporaryDirectory() as one, tempfile.TemporaryDirectory() as two:
            r1 = compile_bundle(snapshot, one); r2 = compile_bundle(snapshot, two)
            deterministic = r1 == r2 and all((Path(one) / f).read_bytes() == (Path(two) / f).read_bytes() for f in r1)
        payload = {"status": "PASS" if report["status"] == "PASS" and deterministic else "FAIL", "prototype_count": len(snapshot.prototypes), "assessment_count": len(a["assessments"]), "m_minus_count": len(a["m_minus"]), "selected_count": p["selected_count"], "bundle_deterministic": deterministic, "audit_status": report["status"], "snapshot_sha256": snapshot.sha256, "analysis_sha256": a["analysis_sha256"], "plan_sha256": p["plan_sha256"], "external_action_performed": False, "truth_probability_claimed": False}
        _write_or_print(payload, args.output); return 0 if payload["status"] == "PASS" else 2
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
