from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .job_system import audit_job_campaign, compile_job_campaign, replay_job


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-problem-jobs",
        description="Run, resume, replay and audit allowlisted deterministic research jobs.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    compile_parser = sub.add_parser("compile", help="execute or checkpoint a job campaign")
    compile_parser.add_argument("--bundle-json", required=True)
    compile_parser.add_argument("--output-dir", required=True)
    compile_parser.add_argument("--max-jobs", type=int)
    compile_parser.add_argument("--resume", action="store_true")

    audit_parser = sub.add_parser("audit", help="strictly replay-audit a campaign")
    audit_parser.add_argument("output_dir")

    replay_parser = sub.add_parser("replay", help="replay one materialized job")
    campaign_group = replay_parser.add_mutually_exclusive_group(required=True)
    campaign_group.add_argument("--campaign-dir")
    campaign_group.add_argument("--campaign-id")
    replay_parser.add_argument("--search-root", default=".")
    replay_parser.add_argument("--job-id", required=True)
    return parser


def _resolve_campaign_dir(campaign_id: str, search_root: Path) -> Path:
    matches: list[Path] = []
    for manifest_path in sorted(search_root.rglob("manifest.json")):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if manifest.get("campaign_id") == campaign_id:
            matches.append(manifest_path.parent)
            if len(matches) > 1:
                break
    if len(matches) != 1:
        raise ValueError(
            f"campaign_id must resolve to exactly one local campaign under {search_root}: "
            f"{campaign_id} ({len(matches)} matches)"
        )
    return matches[0]


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "compile":
        result = compile_job_campaign(
            Path(args.bundle_json),
            Path(args.output_dir),
            max_jobs=args.max_jobs,
            resume=args.resume,
        )
    elif args.command == "audit":
        result = audit_job_campaign(Path(args.output_dir))
    else:
        campaign_dir = (
            Path(args.campaign_dir)
            if args.campaign_dir
            else _resolve_campaign_dir(args.campaign_id, Path(args.search_root))
        )
        result = replay_job(campaign_dir, args.job_id)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("valid", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
