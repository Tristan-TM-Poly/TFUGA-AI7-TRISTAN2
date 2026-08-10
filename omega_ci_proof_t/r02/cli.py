from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .constitution import AutonomyConstitution
from .coverage import ClaimCoverageEngine
from .expiry import EvidenceExpiryEngine
from .models import ClaimCoverage, EvidenceValidity, SemanticProofKey
from .oak import run_oakbench
from .promotion import PromotionProofBuilder, PromotionProofVerifier
from .supply_chain import SupplyChainAuditor


def read_json(path: str) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str, value: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="omega-ci-proof-r02")
    sub = root.add_subparsers(dest="command", required=True)
    expiry = sub.add_parser("expiry")
    expiry.add_argument("--bundle", required=True); expiry.add_argument("--claims", required=True)
    expiry.add_argument("--observed-at", required=True); expiry.add_argument("--evaluated-at", required=True)
    expiry.add_argument("--changed-package", action="append", default=[]); expiry.add_argument("--changed-dependency", action="append", default=[])
    expiry.add_argument("--changed-environment", action="append", default=[]); expiry.add_argument("--changed-test", action="append", default=[])
    expiry.add_argument("--superseded-by", default=""); expiry.add_argument("--revoked", action="store_true"); expiry.add_argument("--output")
    coverage = sub.add_parser("coverage")
    coverage.add_argument("--claims", required=True); coverage.add_argument("--tests", required=True); coverage.add_argument("--results", required=True); coverage.add_argument("--output")
    promotion = sub.add_parser("promotion")
    promotion.add_argument("--claim-id", required=True); promotion.add_argument("--from-status", required=True); promotion.add_argument("--to-status", required=True)
    promotion.add_argument("--validity", required=True); promotion.add_argument("--coverage", required=True); promotion.add_argument("--bundle-id", action="append", default=[]); promotion.add_argument("--output")
    verify = sub.add_parser("verify-promotion"); verify.add_argument("--proof", required=True)
    constitution = sub.add_parser("constitution"); constitution.add_argument("--file", required=True)
    capability = sub.add_parser("capability")
    capability.add_argument("--constitution", required=True); capability.add_argument("--agent", required=True); capability.add_argument("--run-id", required=True); capability.add_argument("--level", default="A3")
    capability.add_argument("--action", action="append", default=[]); capability.add_argument("--scope", action="append", default=[]); capability.add_argument("--issued-at", required=True); capability.add_argument("--expires-at", required=True); capability.add_argument("--output")
    supply = sub.add_parser("supply-chain"); supply.add_argument("paths", nargs="+")
    cache_key = sub.add_parser("cache-key")
    for field in ("claim-digest", "code-slice-digest", "dependency-digest", "environment-class", "test-digest"):
        cache_key.add_argument(f"--{field}", required=True)
    sub.add_parser("oak")
    return root


def _claims(raw: object) -> list[dict[str, object]]:
    if isinstance(raw, dict) and isinstance(raw.get("claims"), list):
        return list(raw["claims"])
    if isinstance(raw, list):
        return list(raw)
    raise TypeError("claims must be a list or registry object")


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "expiry":
        value = EvidenceExpiryEngine().evaluate(read_json(args.bundle), _claims(read_json(args.claims)), observed_at=args.observed_at, evaluated_at=args.evaluated_at, changed_packages=args.changed_package, changed_dependencies=args.changed_dependency, changed_environments=args.changed_environment, changed_tests=args.changed_test, superseded_by=args.superseded_by, revoked=args.revoked)
        payload = value.to_dict(); print(json.dumps(payload, indent=2, sort_keys=True))
        if args.output: write_json(args.output, payload)
        return 0
    if args.command == "coverage":
        results_raw = read_json(args.results); results = results_raw.get("test_results", results_raw) if isinstance(results_raw, dict) else results_raw
        tests_raw = read_json(args.tests); tests = tests_raw.get("tests", tests_raw) if isinstance(tests_raw, dict) else tests_raw
        report = ClaimCoverageEngine().evaluate(_claims(read_json(args.claims)), tests, results)
        payload = report.to_dict(); print(json.dumps(payload, indent=2, sort_keys=True))
        if args.output: write_json(args.output, payload)
        return 0 if report.blocked_claims == 0 else 1
    if args.command == "promotion":
        validity_raw = read_json(args.validity); coverage_raw = read_json(args.coverage)
        validity = EvidenceValidity(bundle_id=str(validity_raw["bundle_id"]), claim_ids=tuple(validity_raw.get("claim_ids", [])), observed_at=str(validity_raw["observed_at"]), evaluated_at=str(validity_raw["evaluated_at"]), expires_at=str(validity_raw["expires_at"]), status=str(validity_raw["status"]), reasons=tuple(validity_raw.get("reasons", [])), invalidated_by=tuple(validity_raw.get("invalidated_by", [])), refresh_requirements=tuple(validity_raw.get("refresh_requirements", [])), source_digest=str(validity_raw["source_digest"]))
        claim_rows = coverage_raw.get("claims", [])
        row = next(item for item in claim_rows if item["claim_id"] == args.claim_id)
        coverage = ClaimCoverage(claim_id=str(row["claim_id"]), required_kinds=tuple(row.get("required_kinds", [])), observed_kinds=tuple(row.get("observed_kinds", [])), missing_kinds=tuple(row.get("missing_kinds", [])), dimensions=dict(row.get("dimensions", {})), score=float(row["score"]), weight=float(row.get("weight", 1.0)), blocked=bool(row["blocked"]), reasons=tuple(row.get("reasons", [])))
        proof = PromotionProofBuilder().build(claim_id=args.claim_id, from_status=args.from_status, to_status=args.to_status, validity=[validity], coverage=coverage, evidence_bundle_ids=args.bundle_id, evidence_integrity_verified=True, no_critical_residuals=True)
        payload = proof.to_dict(); print(json.dumps(payload, indent=2, sort_keys=True))
        if args.output: write_json(args.output, payload)
        return 0 if proof.decision == "ELIGIBLE_FOR_HUMAN_REVIEW" else 2
    if args.command == "verify-promotion":
        ok, errors = PromotionProofVerifier().verify(read_json(args.proof)); print(json.dumps({"valid": ok, "errors": list(errors)}, indent=2, sort_keys=True)); return 0 if ok else 1
    if args.command == "constitution":
        audit = AutonomyConstitution(read_json(args.file)).audit(); print(json.dumps(audit.to_dict(), indent=2, sort_keys=True)); return 0 if audit.passed else 1
    if args.command == "capability":
        token = AutonomyConstitution(read_json(args.constitution)).issue_token(agent=args.agent, run_id=args.run_id, level=args.level, requested_actions=args.action, scope=args.scope, issued_at=args.issued_at, expires_at=args.expires_at)
        payload = token.to_dict(); print(json.dumps(payload, indent=2, sort_keys=True))
        if args.output: write_json(args.output, payload)
        return 0
    if args.command == "supply-chain":
        findings = [item.to_dict() for path in args.paths for item in SupplyChainAuditor().audit_path(path)]; print(json.dumps({"findings": findings}, indent=2, sort_keys=True)); return 1 if any(item["severity"] == "error" for item in findings) else 0
    if args.command == "cache-key":
        key = SemanticProofKey(args.claim_digest, args.code_slice_digest, args.dependency_digest, args.environment_class, args.test_digest); print(json.dumps(key.to_dict(), indent=2, sort_keys=True)); return 0
    if args.command == "oak":
        result = run_oakbench(); print(json.dumps(result, indent=2, sort_keys=True)); return 0 if result["passed"] else 1
    raise AssertionError("unreachable")

if __name__ == "__main__":
    sys.exit(main())
