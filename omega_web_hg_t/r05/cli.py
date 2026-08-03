"""CLI for Ω-WEB-HG-T∞ R0.5 Policy Compiler."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .builtin_policies import BUILTIN_POLICIES, policy_by_id
from .compiler import compare_compiled_policies, compile_policy, load_profile, write_compiled, write_profile
from .gate import PolicyGate, RequestContext
from .registry import PolicyRegistry


def _emit(payload: Any, output: str | None = None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def _parse_env(values: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"environment entry must be NAME=VALUE: {value}")
        key, item = value.split("=", 1)
        if not key.strip():
            raise ValueError("environment variable name cannot be empty")
        result[key.strip()] = item
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-web-hg-r05", description="Executable Web policy compiler and OAK gates")
    commands = parser.add_subparsers(dest="command", required=True)

    catalog = commands.add_parser("catalog")
    catalog.add_argument("--as-of", default="2026-08-03")
    catalog.add_argument("--output")

    compile_command = commands.add_parser("compile")
    compile_command.add_argument("source_id")
    compile_command.add_argument("--as-of", default="2026-08-03")
    compile_command.add_argument("--output")

    compile_file = commands.add_parser("compile-file")
    compile_file.add_argument("profile")
    compile_file.add_argument("--as-of", default="2026-08-03")
    compile_file.add_argument("--output")

    gate_record = commands.add_parser("gate-record")
    gate_record.add_argument("source_id")
    gate_record.add_argument("record")
    gate_record.add_argument("--mode", choices=("reject", "redact"))
    gate_record.add_argument("--as-of", default="2026-08-03")
    gate_record.add_argument("--output")

    gate_request = commands.add_parser("gate-request")
    gate_request.add_argument("source_id")
    gate_request.add_argument("route")
    gate_request.add_argument("--rps", type=float, default=1.0)
    gate_request.add_argument("--user-agent", default="Omega-Web-HG-R05/0.5")
    gate_request.add_argument("--contact-email")
    gate_request.add_argument("--env", action="append", default=[])
    gate_request.add_argument("--as-of", default="2026-08-03")
    gate_request.add_argument("--output")

    materialize = commands.add_parser("materialize")
    materialize.add_argument("--output-dir", default="generated/omega_web_hg_r05")
    materialize.add_argument("--as-of", default="2026-08-03")

    drift = commands.add_parser("drift")
    drift.add_argument("old_profile")
    drift.add_argument("new_profile")
    drift.add_argument("--as-of", default="2026-08-03")
    drift.add_argument("--output")

    audit = commands.add_parser("audit")
    audit.add_argument("--as-of", default="2026-08-03")
    audit.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "catalog":
        rows = []
        for profile in BUILTIN_POLICIES:
            compiled = compile_policy(profile, as_of=args.as_of)
            rows.append(
                {
                    "source_id": profile.source_id,
                    "policy_status": profile.policy_status,
                    "review_status": compiled.review_status,
                    "review_reasons": list(compiled.review_reasons),
                    "allowed_routes": list(compiled.allowed_routes),
                    "required_environment": list(compiled.required_environment),
                    "profile_digest": profile.digest,
                    "policy_digest": compiled.policy_digest,
                }
            )
        _emit(rows, args.output)
        return 0

    if args.command == "compile":
        _emit(compile_policy(policy_by_id(args.source_id), as_of=args.as_of).to_dict(), args.output)
        return 0

    if args.command == "compile-file":
        _emit(compile_policy(load_profile(args.profile), as_of=args.as_of).to_dict(), args.output)
        return 0

    if args.command == "gate-record":
        record = json.loads(Path(args.record).read_text(encoding="utf-8"))
        if not isinstance(record, dict):
            raise ValueError("record must be a JSON object")
        decision = PolicyGate(compile_policy(policy_by_id(args.source_id), as_of=args.as_of)).evaluate_record(record, mode=args.mode)
        _emit(decision.to_dict(), args.output)
        return 0 if decision.allowed else 2

    if args.command == "gate-request":
        environment = _parse_env(args.env)
        headers = {"User-Agent": args.user_agent} if args.user_agent else {}
        context = RequestContext(
            route=args.route,
            headers=headers,
            environment=environment,
            requested_rps=args.rps,
            contact_email=args.contact_email,
        )
        decision = PolicyGate(compile_policy(policy_by_id(args.source_id), as_of=args.as_of)).evaluate_request(context)
        _emit(decision.to_dict(), args.output)
        return 0 if decision.allowed else 2

    if args.command == "materialize":
        root = Path(args.output_dir)
        profiles_dir = root / "profiles"
        compiled_dir = root / "compiled"
        registry_path = root / "policy-registry.sqlite3"
        root.mkdir(parents=True, exist_ok=True)
        with PolicyRegistry(registry_path) as registry:
            for profile in BUILTIN_POLICIES:
                compiled = compile_policy(profile, as_of=args.as_of)
                write_profile(profile, profiles_dir / f"{profile.source_id}.json")
                write_compiled(compiled, compiled_dir / f"{profile.source_id}.json")
                registry.record_profile(profile)
                registry.record_compiled(compiled)
            exported = registry.export_jsonl(root / "registry-export")
            manifest = {
                "schema": "omega-web-hg-r05-materialization/1.0",
                "as_of": args.as_of,
                "source_count": len(BUILTIN_POLICIES),
                "pass_count": sum(compile_policy(item, as_of=args.as_of).review_status == "pass" for item in BUILTIN_POLICIES),
                "human_review_count": sum(compile_policy(item, as_of=args.as_of).review_status == "human_review" for item in BUILTIN_POLICIES),
                "fail_count": sum(compile_policy(item, as_of=args.as_of).review_status == "fail" for item in BUILTIN_POLICIES),
                "registry_counts": registry.counts(),
                "exports": [str(path.relative_to(root)) for path in exported],
                "policy_document_is_executable_permission": False,
                "compiled_policy_is_legal_advice": False,
            }
        _emit(manifest, str(root / "materialization-manifest.json"))
        print(root / "materialization-manifest.json")
        return 0

    if args.command == "drift":
        old = compile_policy(load_profile(args.old_profile), as_of=args.as_of)
        new = compile_policy(load_profile(args.new_profile), as_of=args.as_of)
        report = compare_compiled_policies(old, new)
        _emit(report, args.output)
        return 2 if report["requires_human_review"] else 0

    rows = [compile_policy(profile, as_of=args.as_of) for profile in BUILTIN_POLICIES]
    failures: list[str] = []
    for policy in rows:
        if policy.source_id != "arxiv" and policy.review_status != "pass":
            failures.append(f"{policy.source_id}:{policy.review_status}")
        if policy.source_id == "arxiv" and policy.review_status != "human_review":
            failures.append("arxiv_must_remain_human_review")
        if policy.retention_rules.get("raw_response") != "forbidden":
            failures.append(f"{policy.source_id}:raw_response_not_forbidden")
        if not {"abstract", "body", "full_text"}.issubset(set(policy.forbidden_fields)):
            failures.append(f"{policy.source_id}:critical_forbidden_fields_missing")
    payload = {
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "as_of": args.as_of,
        "source_count": len(rows),
        "pass_count": sum(item.review_status == "pass" for item in rows),
        "human_review_count": sum(item.review_status == "human_review" for item in rows),
        "policy_digests": {item.source_id: item.policy_digest for item in rows},
        "legal_advice_claimed": False,
        "permission_beyond_profile_claimed": False,
    }
    _emit(payload, args.output)
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
