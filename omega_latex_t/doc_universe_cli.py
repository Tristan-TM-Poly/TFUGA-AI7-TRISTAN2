"""CLI for Ω-DOC-COMPILER-T R0.3."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .doc_universe import scan_repository, write_bundle


def _load_statuses(path: str | None) -> dict[str, str]:
    if not path:
        return {}
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("status map must be a JSON object")
    return {str(k): str(v) for k, v in payload.items()}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="omega-doc-universe",
        description="Compile evidence-bound D0-D5 repository documentation from observable facts.",
    )
    p.add_argument("repo", nargs="?", default=".")
    p.add_argument("--output-dir", default="generated/omega_doc_universe")
    p.add_argument("--source-commit", default="")
    p.add_argument("--declared-statuses")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    report = scan_repository(
        args.repo,
        source_commit=args.source_commit,
        declared_statuses=_load_statuses(args.declared_statuses),
    )
    manifest = write_bundle(report, args.output_dir)
    print(json.dumps({
        "schema_version": report["schema_version"],
        "system_count": report["system_count"],
        "output_dir": str(Path(args.output_dir)),
        "manifest_files": len(manifest["files"]),
        "truth_boundary": report["truth_boundary"],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
