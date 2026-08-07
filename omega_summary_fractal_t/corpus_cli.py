from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .corpus import CorpusSummaryEngine, RepositorySpec, discover_local_repositories, load_manifest
from .dashboard import write_dashboard
from .fleet import write_fleet_manifest
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
    p.add_argument("--fleet-salt-env", default="OMEGA_FLEET_SALT", help="Runtime env var containing the private HMAC salt")
    p.add_argument("--require-fleet", action="store_true", help="Fail if the fleet salt is unavailable instead of omitting public fleet output")
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
    output = Path(args.output_dir)
    bundle = CorpusSummaryEngine(specs, max_files=args.max_files).write(
        output,
        depth=args.depth,
        audience=args.audience,
        emit_repository_views=not args.no_repository_views,
    )
    dashboard = write_dashboard(
        output / "CORPUS_SUMMARY.json",
        output / "dashboard",
        index=output / "CORPUS_INDEX.json",
    )

    salt = os.getenv(args.fleet_salt_env, "").strip()
    fleet: dict[str, Path] = {}
    if salt:
        fleet = write_fleet_manifest(output / "CORPUS_SUMMARY.json", output / "fleet", salt=salt)
    elif args.require_fleet:
        raise SystemExit(f"required fleet salt environment variable is missing: {args.fleet_salt_env}")

    print(
        json.dumps(
            {
                "repositories": bundle.totals["repositories"],
                "systems": bundle.totals["systems"],
                "fingerprint": bundle.fingerprint,
                "output_dir": str(output),
                "dashboard": {key: str(value) for key, value in dashboard.items()},
                "fleet_emitted": bool(fleet),
                "fleet": {key: str(value) for key, value in fleet.items()},
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
