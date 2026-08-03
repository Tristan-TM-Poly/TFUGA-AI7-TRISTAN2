from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .intent import IntentCompiler
from .live_github import GitHubReadOnlyScanner
from .models import IntentContract
from .orchestrator import MyceliumOrchestrator
from .snapshot import SnapshotBundle


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-mycelium",
        description="Ω-GITHUB-MYCELIUM-T∞ read-first multi-repository campaign compiler.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    live = sub.add_parser("live-scan", help="Read all owned repositories and open PRs through paginated GitHub REST.")
    live.add_argument("--owner", required=True)
    live.add_argument("--output", required=True)
    live.add_argument("--token-env", default="GITHUB_TOKEN")
    live.add_argument("--timeout-seconds", type=float, default=30.0)

    validate = sub.add_parser("validate-snapshot", help="Validate and summarize an offline snapshot.")
    validate.add_argument("snapshot")

    compile_intent = sub.add_parser("compile", help="Compile an intent JSON and snapshot into a dry-run campaign bundle.")
    compile_intent.add_argument("--intent", required=True)
    compile_intent.add_argument("--snapshot", required=True)
    compile_intent.add_argument("--output-dir", required=True)

    plan = sub.add_parser("plan", help="Compile a textual objective directly against a snapshot.")
    plan.add_argument("--objective", required=True)
    plan.add_argument("--root-creation")
    plan.add_argument("--snapshot", required=True)
    plan.add_argument("--candidate-repository", action="append", default=[])
    plan.add_argument("--output-dir", required=True)
    return parser


def _intent_from_json(path: str) -> IntentContract:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    return IntentContract(
        intent_id=str(value["intent_id"]),
        objective=str(value["objective"]),
        root_creation=str(value["root_creation"]),
        expected_outputs=tuple(value.get("expected_outputs", ())),
        candidate_repositories=tuple(value.get("candidate_repositories", ())),
        constraints=tuple(value.get("constraints", ())),
        success_conditions=tuple(value.get("success_conditions", ())),
        requested_depth_mode=str(value.get("requested_depth_mode", "adaptive")),
        observed_depth_target=value.get("observed_depth_target"),
        author=str(value.get("author", "Tristan")),
        remote_mutations_authorized=bool(value.get("remote_mutations_authorized", False)),
        metadata=dict(value.get("metadata", {})),
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "live-scan":
        snapshot = GitHubReadOnlyScanner.from_environment(
            args.token_env,
            timeout_seconds=args.timeout_seconds,
        ).scan_owner(args.owner)
        snapshot.write(args.output)
        print(json.dumps(snapshot.summary(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if args.command == "validate-snapshot":
        snapshot = SnapshotBundle.read(args.snapshot)
        print(json.dumps(snapshot.summary(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if args.command == "compile":
        intent = _intent_from_json(args.intent)
        snapshot = SnapshotBundle.read(args.snapshot)
        result = MyceliumOrchestrator().compile(intent, snapshot, args.output_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if result["oak"]["blocker_count"] == 0 else 2
    if args.command == "plan":
        snapshot = SnapshotBundle.read(args.snapshot)
        intent = IntentCompiler().compile(
            args.objective,
            root_creation=args.root_creation,
            candidate_repositories=args.candidate_repository,
        )
        result = MyceliumOrchestrator().compile(intent, snapshot, args.output_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if result["oak"]["blocker_count"] == 0 else 2
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
