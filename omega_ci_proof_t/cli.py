from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import sys

from .adversarial import audit_source
from .autonomy import AutonomyGate
from .claims import ClaimRegistry
from .diagnosis import diagnose_pytest_log
from .evidence import EvidenceBundleBuilder, EvidenceVerifier, hash_file
from .generators import MMinusRegressionGenerator
from .io import evidence_bundle_from_mapping, proof_plan_from_mapping, read_json, test_catalog_from_mapping, write_json
from .ledger import ProofLedger
from .models import TestResult, stable_digest
from .oak import run_oakbench
from .planner import ProofPlanner


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-ci-proof", description="Ω-CI-PROOF-AUTONOMY-T∞ A1-A3")
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan")
    plan.add_argument("--impact", required=True)
    plan.add_argument("--claims", required=True)
    plan.add_argument("--tests", required=True)
    plan.add_argument("--output", required=True)

    bundle = sub.add_parser("bundle")
    bundle.add_argument("--plan", required=True)
    bundle.add_argument("--results", required=True)
    bundle.add_argument("--commit-sha", required=True)
    bundle.add_argument("--artifact", action="append", default=[])
    bundle.add_argument("--output", required=True)
    bundle.add_argument("--ledger")

    verify = sub.add_parser("verify")
    verify.add_argument("--bundle", required=True)
    verify.add_argument("--plan")

    generate = sub.add_parser("generate-regressions")
    generate.add_argument("--mminus", required=True)
    generate.add_argument("--output", required=True)

    diagnose = sub.add_parser("diagnose")
    diagnose.add_argument("--log", required=True)
    diagnose.add_argument("--output")

    adversarial = sub.add_parser("adversarial")
    adversarial.add_argument("paths", nargs="+")

    autonomy = sub.add_parser("autonomy")
    autonomy.add_argument("--level", default="A3")
    autonomy.add_argument("--risk", default="low")
    autonomy.add_argument("--irreversible", action="store_true")
    autonomy.add_argument("--public-api-change", action="store_true")
    autonomy.add_argument("--security-sensitive", action="store_true")
    autonomy.add_argument("--ip-sensitive", action="store_true")
    autonomy.add_argument("--financial-effect", action="store_true")

    oak = sub.add_parser("oak")
    oak.add_argument("--ledger")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "plan":
        impact = read_json(args.impact)
        registry = ClaimRegistry.from_json(args.claims)
        catalog = test_catalog_from_mapping(read_json(args.tests))
        plan = ProofPlanner(registry, catalog).plan(impact)
        write_json(args.output, plan.to_dict())
        print(plan.plan_id)
        return 0

    if args.command == "bundle":
        plan = proof_plan_from_mapping(read_json(args.plan))
        results_raw = read_json(args.results)
        results = tuple(TestResult(**item) for item in results_raw["test_results"])
        properties = dict(results_raw.get("properties", {}))
        artifacts = tuple(hash_file(path) for path in args.artifact)
        bundle = EvidenceBundleBuilder().build(
            plan,
            run_id=str(results_raw.get("run_id", "CI-LOCAL")),
            commit_sha=args.commit_sha,
            environment={"python": platform.python_version(), "platform": platform.platform()},
            test_results=results,
            properties=properties,
            artifacts=artifacts,
        )
        write_json(args.output, bundle.to_dict())
        if args.ledger:
            ProofLedger(args.ledger).append(bundle.to_dict())
        print(bundle.bundle_id)
        return 0

    if args.command == "verify":
        raw_bundle = read_json(args.bundle)
        required = []
        if args.plan:
            required = [test.test_id for test in proof_plan_from_mapping(read_json(args.plan)).tests]
        ok, errors = EvidenceVerifier().verify_serialized(raw_bundle, required_test_ids=required)
        print(json.dumps({"valid": ok, "errors": list(errors)}, indent=2, sort_keys=True))
        return 0 if ok else 1

    if args.command == "generate-regressions":
        generator = MMinusRegressionGenerator()
        source = generator.generate(generator.load(args.mminus))
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")
        print(stable_digest(source))
        return 0

    if args.command == "diagnose":
        diagnostic = diagnose_pytest_log(Path(args.log).read_text(encoding="utf-8", errors="replace"))
        payload = diagnostic.to_dict()
        if args.output:
            write_json(args.output, payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "adversarial":
        findings = [finding.to_dict() for path in args.paths for finding in audit_source(path)]
        print(json.dumps({"findings": findings}, indent=2, sort_keys=True))
        return 1 if any(item["severity"] == "error" for item in findings) else 0

    if args.command == "autonomy":
        decision = AutonomyGate().evaluate(
            args.level,
            risk=args.risk,
            reversible=not args.irreversible,
            public_api_change=args.public_api_change,
            security_sensitive=args.security_sensitive,
            ip_sensitive=args.ip_sensitive,
            financial_effect=args.financial_effect,
        )
        print(json.dumps(decision.to_dict(), indent=2, sort_keys=True))
        return 0 if decision.allowed else 2

    if args.command == "oak":
        result = run_oakbench(ledger_path=args.ledger)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["passed"] else 1

    raise AssertionError("unreachable")


if __name__ == "__main__":
    sys.exit(main())
