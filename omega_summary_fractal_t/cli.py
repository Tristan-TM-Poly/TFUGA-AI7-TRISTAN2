from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .aliases import approve_alias, identity_proposals, verify_alias_registry
from .dashboard import write_dashboard
from .delta import write_delta
from .export import write_graph_exports
from .fleet import write_fleet_manifest
from .identity import write_identity_report
from .index import append_snapshot, verify_index, write_longitudinal_reports
from .query import query_payload, write_query
from .query_plan import execute_query_plan, write_query_plan
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

    identity = subparsers.add_parser("identity")
    identity.add_argument("previous", help="previous D9 summary JSON")
    identity.add_argument("current", help="current D9 summary JSON")
    identity.add_argument("--min-overlap", type=float, default=0.80)
    identity.add_argument("--output-dir", default=".omega/identity-continuity")

    alias_proposals = subparsers.add_parser("alias-proposals")
    alias_proposals.add_argument("identity_report", help="IDENTITY_CONTINUITY.json")
    alias_proposals.add_argument("--output", default=".omega/identity-continuity/ALIAS_PROPOSALS.json")

    alias_approve = subparsers.add_parser("alias-approve")
    alias_approve.add_argument("source")
    alias_approve.add_argument("target")
    alias_approve.add_argument("--registry", default=".omega/aliases/ALIAS_REGISTRY.json")
    alias_approve.add_argument("--evidence-ref", required=True)
    alias_approve.add_argument("--approved-by", required=True)
    alias_approve.add_argument("--note", default="")

    index = subparsers.add_parser("index")
    index.add_argument("summary", help="repository or corpus summary JSON snapshot")
    index.add_argument("--index-file", default=".omega/corpus-index.json")
    index.add_argument("--report-dir", default=".omega/longitudinal")

    export = subparsers.add_parser("export")
    export.add_argument("summary", help="repository summary JSON snapshot")
    export.add_argument("--output-dir", default=".omega/graph-export")

    query = subparsers.add_parser("query")
    query.add_argument("source", help="repository summary, corpus summary, or longitudinal index JSON")
    query.add_argument("--text")
    query.add_argument("--kind")
    query.add_argument("--status")
    query.add_argument("--relation")
    query.add_argument("--repository")
    query.add_argument("--min-crystallization", type=float)
    query.add_argument("--max-crystallization", type=float)
    query.add_argument("--limit", type=int, default=100)
    query.add_argument("--output-dir")

    query_plan = subparsers.add_parser("query-plan")
    query_plan.add_argument("source", help="repository summary, corpus summary, or longitudinal index JSON")
    query_plan.add_argument("plan", help="declarative JSON query plan")
    query_plan.add_argument("--output-dir")

    dashboard = subparsers.add_parser("dashboard")
    dashboard.add_argument("summary", help="repository or corpus summary JSON")
    dashboard.add_argument("--index-file")
    dashboard.add_argument("--top-n", type=int, default=20)
    dashboard.add_argument("--output-dir", default=".omega/dashboard")

    fleet = subparsers.add_parser("fleet")
    fleet.add_argument("source", help="repository/corpus/index JSON source")
    fleet.add_argument("--salt-env", default="OMEGA_FLEET_SALT")
    fleet.add_argument("--salt-file")
    fleet.add_argument("--output-dir", default=".omega/fleet")

    return parser


def _resolve_fleet_salt(args: argparse.Namespace) -> str:
    if getattr(args, "salt_file", None):
        value = Path(args.salt_file).read_text(encoding="utf-8").strip()
    else:
        value = os.getenv(getattr(args, "salt_env", "OMEGA_FLEET_SALT"), "").strip()
    if not value:
        raise SystemExit("fleet salt missing; use --salt-file or set the selected runtime environment variable")
    return value


def _write_r04_views(bundle, output_dir: str | Path) -> dict[str, Path]:
    out = Path(output_dir)
    history = out / "SUMMARY_HISTORY.json"
    index = append_snapshot(history, bundle.to_dict())
    if not verify_index(index):
        raise ValueError("summary history hash chain is invalid after append")
    generated = {"history": history}
    generated.update(write_longitudinal_reports(history, out / "longitudinal"))
    generated.update({f"graph_{key}": value for key, value in write_graph_exports(bundle.to_dict(), out / "graph").items()})
    generated.update({f"dashboard_{key}": value for key, value in write_dashboard(bundle.to_dict(), out / "dashboard", index=history).items()})
    return generated


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
        if args.depth == 9:
            paths.update(_write_r04_views(bundle, args.output_dir))
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
    r04_artifacts: dict[str, str] = {}
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
            r04_artifacts = {key: str(value) for key, value in _write_r04_views(bundle, out).items()}
    (out / "depth_index.json").write_text(
        json.dumps(index, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {"generated_depths": 10, "output_dir": str(out), "r04_artifacts": r04_artifacts},
            sort_keys=True,
        )
    )
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


def cmd_identity(args: argparse.Namespace) -> int:
    paths = write_identity_report(
        args.previous,
        args.current,
        args.output_dir,
        min_overlap=args.min_overlap,
    )
    print(json.dumps({key: str(value) for key, value in paths.items()}, sort_keys=True))
    return 0


def cmd_alias_proposals(args: argparse.Namespace) -> int:
    report = identity_proposals(args.identity_report)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"proposal_count": len(report["proposals"]), "output": str(output)}, sort_keys=True))
    return 0


def cmd_alias_approve(args: argparse.Namespace) -> int:
    registry = approve_alias(
        args.registry,
        source=args.source,
        target=args.target,
        evidence_ref=args.evidence_ref,
        approved_by=args.approved_by,
        note=args.note,
    )
    print(
        json.dumps(
            {
                "registry": str(args.registry),
                "entries": len(registry.get("entries", [])),
                "valid_hash_chain": verify_alias_registry(registry),
            },
            sort_keys=True,
        )
    )
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


def cmd_query(args: argparse.Namespace) -> int:
    report = query_payload(
        args.source,
        text=args.text,
        kind=args.kind,
        status=args.status,
        relation=args.relation,
        repository=args.repository,
        min_crystallization=args.min_crystallization,
        max_crystallization=args.max_crystallization,
        limit=args.limit,
    )
    if args.output_dir:
        paths = write_query(report, args.output_dir)
        print(json.dumps({"total_matches": report["total_matches"], **{key: str(value) for key, value in paths.items()}}, sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


def cmd_query_plan(args: argparse.Namespace) -> int:
    report = execute_query_plan(args.source, args.plan)
    if args.output_dir:
        paths = write_query_plan(report, args.output_dir)
        print(json.dumps({"total_matches": report["total_matches"], **{key: str(value) for key, value in paths.items()}}, sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    paths = write_dashboard(args.summary, args.output_dir, index=args.index_file, top_n=args.top_n)
    print(json.dumps({key: str(value) for key, value in paths.items()}, sort_keys=True))
    return 0


def cmd_fleet(args: argparse.Namespace) -> int:
    paths = write_fleet_manifest(args.source, args.output_dir, salt=_resolve_fleet_salt(args))
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
    if args.command == "identity":
        return cmd_identity(args)
    if args.command == "alias-proposals":
        return cmd_alias_proposals(args)
    if args.command == "alias-approve":
        return cmd_alias_approve(args)
    if args.command == "index":
        return cmd_index(args)
    if args.command == "export":
        return cmd_export(args)
    if args.command == "query":
        return cmd_query(args)
    if args.command == "query-plan":
        return cmd_query_plan(args)
    if args.command == "dashboard":
        return cmd_dashboard(args)
    if args.command == "fleet":
        return cmd_fleet(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
