from __future__ import annotations

import argparse
import json
from pathlib import Path

from .corpus import CorpusSummaryEngine, RepositorySpec, discover_local_repositories, load_manifest
from .summarizer import AUDIENCES


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="omega-summary-corpus", description="Cross-repository Ω-SUMMARY-FRACTAL corpus compiler")
    p.add_argument("--workspace", help="Discover repositories among a workspace and its direct children")
    p.add_argument("--manifest", help="JSON manifest containing repository roots")
    p.add_argument("--repo", action="append", default=[], help="Explicit repository root; repeatable")
    p.add_argument("--depth", type=int, default=4)
    p.add_argument("--audience", choices=sorted(AUDIENCES), default="tristan")
    p.add_argument("--output-dir", default=".omega/corpus-summary")
    p.add_argument("--max-files", type=int, default=20000)
    p.add_argument("--no-repository-views", action="store_true")
    return p


def resolve_specs(args: argparse.Namespace) -> list[RepositorySpec]:
    specs: list[RepositorySpec] = []
    if args.manifest:
        specs.extend(load_manifest(args.manifest))
    if args.workspace:
        specs.extend(discover_local_repositories(args.workspace))
    specs.extend(RepositorySpec(root) for root in args.repo)
    dedup = {str(spec.path): spec for spec in specs}
    return list(dedup.values())


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    specs = resolve_specs(args)
    if not specs:
        raise SystemExit("no repositories resolved; use --workspace, --manifest or --repo")
    bundle = CorpusSummaryEngine(specs, max_files=args.max_files).write(args.output_dir, depth=args.depth, audience=args.audience, emit_repository_views=not args.no_repository_views)
    print(json.dumps({"repositories": bundle.totals["repositories"], "systems": bundle.totals["systems"], "fingerprint": bundle.fingerprint, "output_dir": str(Path(args.output_dir))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
