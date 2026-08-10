"""CLI for Ω-DOC-FACTORY-T∞ R1.0."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .doc_factory import build_factory_report, write_factory_bundle


def _load(path: str | None, default):
    if not path:
        return default
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _statuses(path: str | None) -> dict[str, str]:
    payload = _load(path, {})
    if not isinstance(payload, dict):
        raise ValueError("declared statuses must be a JSON object")
    return {str(k): str(v) for k, v in payload.items()}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="omega-doc-factory",
        description="Compile facts, execution observations, claims, OAK quality, graph projections, delta and D0-D5 documentation.",
    )
    p.add_argument("repo", nargs="?", default=".")
    p.add_argument("--output-dir", default="generated/omega_doc_factory")
    p.add_argument("--source-commit", default="")
    p.add_argument("--declared-statuses")
    p.add_argument("--execution-receipts")
    p.add_argument("--previous-report")
    p.add_argument("--cache-dir", default=".omega-doc-cache")
    p.add_argument("--no-cache", action="store_true")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    report = build_factory_report(
        args.repo,
        source_commit=args.source_commit,
        declared_statuses=_statuses(args.declared_statuses),
        execution_receipts_payload=_load(args.execution_receipts, []),
        previous_report=_load(args.previous_report, None),
        cache_dir=None if args.no_cache else args.cache_dir,
    )
    manifest = write_factory_bundle(report, args.output_dir)
    print(json.dumps({
        "factory_version": report["factory_version"],
        "source_commit": report["source_commit"],
        "system_count": report["system_count"],
        "claim_candidate_count": len(report["claims"]),
        "execution_receipt_count": len(report["execution_receipts"]),
        "graph_node_count": len(report["graph"]["nodes"]),
        "graph_edge_count": len(report["graph"]["edges"]),
        "manifest_file_count": len(manifest["files"]),
        "campaign_fingerprint": report["campaign_fingerprint"],
        "output_dir": str(Path(args.output_dir)),
        "truth_boundary": report["truth_boundary"],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
