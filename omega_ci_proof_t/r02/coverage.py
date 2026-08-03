from __future__ import annotations

from typing import Any, Mapping, Sequence

from .models import ClaimCoverage, ClaimCoverageReport, sorted_unique

_DIMENSION_WEIGHTS = {
    "positive_test": 0.15,
    "negative_test": 0.15,
    "oracle": 0.15,
    "falsifier": 0.15,
    "provenance": 0.15,
    "environment": 0.10,
    "limitation": 0.05,
    "required_kinds": 0.10,
}

_NEGATIVE_KINDS = {"negative", "adversarial", "mutation", "counterexample", "chaos"}
_ORACLE_KINDS = {"property", "differential", "formal", "schema", "metamorphic"}
_FALSIFIER_KINDS = {"property", "adversarial", "mutation", "counterexample", "differential"}


class ClaimCoverageEngine:
    def evaluate(
        self,
        claims: Sequence[Mapping[str, Any]],
        tests: Sequence[Mapping[str, Any]],
        results: Sequence[Mapping[str, Any]],
        *,
        bundle_limitations: Sequence[str] = (),
    ) -> ClaimCoverageReport:
        test_by_id = {str(item["test_id"]): item for item in tests}
        result_by_id = {str(item["test_id"]): item for item in results}
        coverage_items: list[ClaimCoverage] = []

        for claim in sorted(claims, key=lambda item: str(item["claim_id"])):
            claim_id = str(claim["claim_id"])
            required_ids = tuple(str(value) for value in claim.get("required_test_ids", ()))
            claim_tests = [test_by_id[test_id] for test_id in required_ids if test_id in test_by_id]
            required_kinds = sorted_unique(tuple(str(value) for value in claim.get("required_evidence", ())) or tuple(str(test.get("kind", "unit")) for test in claim_tests))
            observed_kinds = sorted_unique(tuple(
                str(test.get("kind", "unit"))
                for test in claim_tests
                if result_by_id.get(str(test["test_id"]), {}).get("status") == "PASSED"
            ))
            missing_kinds = tuple(kind for kind in required_kinds if kind not in observed_kinds)
            statuses = {test_id: str(result_by_id.get(test_id, {}).get("status", "MISSING")) for test_id in required_ids}
            source_links = all(claim_id in tuple(str(value) for value in test.get("source_claim_ids", ())) for test in claim_tests) if claim_tests else False
            environments = [str(result_by_id.get(test_id, {}).get("environment", "")) for test_id in required_ids if test_id in result_by_id]
            kinds = set(observed_kinds)
            dimensions = {
                "positive_test": any(kind not in _NEGATIVE_KINDS for kind in kinds),
                "negative_test": bool(kinds.intersection(_NEGATIVE_KINDS)),
                "oracle": bool(kinds.intersection(_ORACLE_KINDS)),
                "falsifier": bool(kinds.intersection(_FALSIFIER_KINDS)) or bool(claim.get("falsifiers")),
                "provenance": source_links,
                "environment": bool(environments) and all(environments),
                "limitation": bool(claim.get("domain_of_validity") or claim.get("exclusions") or bundle_limitations),
                "required_kinds": not missing_kinds,
            }
            score = round(sum(_DIMENSION_WEIGHTS[key] for key, value in dimensions.items() if value), 6)
            failed = sorted(test_id for test_id, status in statuses.items() if status != "PASSED")
            reasons: list[str] = []
            if missing_kinds:
                reasons.append(f"missing evidence kinds: {', '.join(missing_kinds)}")
            if failed:
                reasons.append(f"required tests not passed: {', '.join(failed)}")
            if not source_links:
                reasons.append("claim-to-test provenance incomplete")
            weight = float(claim.get("criticality_weight", 1.0))
            blocked = bool(missing_kinds or failed or not source_links)
            coverage_items.append(ClaimCoverage(
                claim_id=claim_id,
                required_kinds=required_kinds,
                observed_kinds=observed_kinds,
                missing_kinds=missing_kinds,
                dimensions=dimensions,
                score=score,
                weight=weight,
                blocked=blocked,
                reasons=tuple(reasons or ["claim has traceable evidence coverage"]),
            ))

        total_weight = sum(item.weight for item in coverage_items)
        weighted = round(sum(item.score * item.weight for item in coverage_items) / total_weight, 6) if total_weight else 0.0
        covered = sum(1 for item in coverage_items if not item.blocked and item.score >= 0.8)
        blocked = sum(1 for item in coverage_items if item.blocked)
        return ClaimCoverageReport(
            claims=tuple(coverage_items),
            weighted_score=weighted,
            covered_claims=covered,
            blocked_claims=blocked,
            uncovered_claims=len(coverage_items) - covered,
        )
