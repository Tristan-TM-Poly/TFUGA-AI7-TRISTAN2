from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import (
    DriveLinkResolver,
    GitHubSyncPlanner,
    HypergraphBuilder,
    ManifestBuilder,
    PermissionPolicy,
    read_links,
    write_json,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ω-DRIVE-GITHUB-ABSORB-T package CLI")
    parser.add_argument("links_file", type=Path, help="Text file containing Google Drive links, one per line")
    parser.add_argument("--repo", default="Tristan-TM-Poly/TFUGA-AI7-TRISTAN2", help="GitHub repo target")
    parser.add_argument("--out", type=Path, default=Path("generated/omega_drive_github_absorb"), help="Output folder")
    parser.add_argument("--level", default="L1", choices=["L0", "L1", "L2", "L3", "L4", "L5", "L6", "L7"], help="Requested OAK level")
    parser.add_argument("--max-level", default="L1", choices=["L0", "L1", "L2", "L3", "L4", "L5", "L6", "L7"], help="Maximum policy level")
    parser.add_argument("--allow-download", action="store_true", help="Allow private download planning for L2/L3")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    policy = PermissionPolicy(max_level=args.max_level, allow_download=args.allow_download)
    links = read_links(args.links_file)
    objects = [DriveLinkResolver.resolve(url) for url in links]
    manifest = ManifestBuilder.build(objects, policy, requested_level=args.level)
    hypergraph = HypergraphBuilder.from_manifest(manifest)
    plan = GitHubSyncPlanner.build_plan(manifest, args.repo)
    oak_report = {
        "system": "Ω-DRIVE-GITHUB-ABSORB-T",
        "requested_level": args.level,
        "max_level": args.max_level,
        "verdict": policy.gate(args.level),
        "dangerous_actions_blocked": True,
        "publication_allowed": False,
        "delete_allowed": False,
        "permission_change_allowed": False,
        "default_branch_push_allowed": False,
        "objects_count": len(objects),
        "unknown_links": [obj.source_url for obj in objects if obj.kind == "unknown"],
        "high_risk_objects": [row["source_url_sha256"] for row in manifest if row["risk_level"] == "high"],
    }

    write_json(args.out / "drive_manifest.json", manifest)
    write_json(args.out / "github_sync_plan.json", plan)
    write_json(args.out / "theory_seed_hypergraph.json", hypergraph)
    write_json(args.out / "oak_report.json", oak_report)

    print(json.dumps(oak_report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
