from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping, Sequence

from .models import EvidenceValidity, sorted_unique, stable_digest


def parse_time(value: str) -> datetime:
    text = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class EvidenceExpiryEngine:
    def evaluate(
        self,
        bundle: Mapping[str, Any],
        claims: Sequence[Mapping[str, Any]],
        *,
        observed_at: str,
        evaluated_at: str,
        changed_packages: Iterable[str] = (),
        changed_dependencies: Iterable[str] = (),
        changed_environments: Iterable[str] = (),
        changed_tests: Iterable[str] = (),
        superseded_by: str = "",
        revoked: bool = False,
    ) -> EvidenceValidity:
        observed = parse_time(observed_at)
        evaluated = parse_time(evaluated_at)
        bundle_claims = tuple(str(value) for value in bundle.get("claims_tested", ()))
        claim_by_id = {str(item.get("claim_id")): item for item in claims}
        ttls = [int(claim_by_id.get(claim_id, {}).get("evidence_ttl_days", 30)) for claim_id in bundle_claims]
        ttl_days = min(ttls) if ttls else 30
        expires = observed + timedelta(days=ttl_days)

        changed_packages_set = set(str(value) for value in changed_packages)
        changed_dependencies_set = set(str(value) for value in changed_dependencies)
        changed_environments_set = set(str(value) for value in changed_environments)
        changed_tests_set = set(str(value) for value in changed_tests)
        reasons: list[str] = []
        invalidators: list[str] = []
        refresh: list[str] = []

        subject_packages = set(str(value) for value in bundle.get("subject", {}).get("affected_packages", ()))
        required_tests: set[str] = set()
        assumptions: set[str] = set()
        for claim_id in bundle_claims:
            claim = claim_by_id.get(claim_id, {})
            required_tests.update(str(value) for value in claim.get("required_test_ids", ()))
            assumptions.update(str(value) for value in claim.get("assumptions", ()))

        if revoked:
            status = "REVOKED"
            reasons.append("evidence was explicitly revoked")
            invalidators.append("revocation")
            refresh.append("human_review")
        elif superseded_by:
            status = "SUPERSEDED"
            reasons.append(f"superseded by {superseded_by}")
            invalidators.append(superseded_by)
            refresh.append("use_superseding_bundle")
        elif changed_packages_set.intersection(subject_packages):
            status = "INVALIDATED"
            touched = sorted(changed_packages_set.intersection(subject_packages))
            reasons.append(f"subject package changed: {', '.join(touched)}")
            invalidators.extend(f"package:{item}" for item in touched)
            refresh.extend(("focused_tests", "artifact_rehash", "new_evidence_bundle"))
        elif changed_tests_set.intersection(required_tests):
            status = "INVALIDATED"
            touched = sorted(changed_tests_set.intersection(required_tests))
            reasons.append(f"required test changed: {', '.join(touched)}")
            invalidators.extend(f"test:{item}" for item in touched)
            refresh.extend(("rerun_changed_tests", "new_evidence_bundle"))
        elif changed_dependencies_set or changed_environments_set:
            status = "STALE"
            if changed_dependencies_set:
                reasons.append("dependency context changed")
                invalidators.extend(f"dependency:{item}" for item in sorted(changed_dependencies_set))
                refresh.append("integration_tests")
            if changed_environments_set:
                reasons.append("environment context changed")
                invalidators.extend(f"environment:{item}" for item in sorted(changed_environments_set))
                refresh.append("environment_reproduction")
        elif evaluated > expires:
            status = "EXPIRED"
            reasons.append("evidence TTL elapsed")
            invalidators.append(f"ttl:{ttl_days}d")
            refresh.extend(("rerun_required_tests", "new_evidence_bundle"))
        else:
            status = "CURRENT"
            reasons.append("no invalidator observed and TTL remains active")

        source_digest = stable_digest({
            "bundle": dict(bundle),
            "claims": [dict(item) for item in claims],
            "assumptions": sorted(assumptions),
        })
        return EvidenceValidity(
            bundle_id=str(bundle.get("bundle_id", "UNKNOWN-BUNDLE")),
            claim_ids=sorted_unique(bundle_claims),
            observed_at=iso_time(observed),
            evaluated_at=iso_time(evaluated),
            expires_at=iso_time(expires),
            status=status,
            reasons=tuple(reasons),
            invalidated_by=sorted_unique(invalidators),
            refresh_requirements=sorted_unique(refresh),
            source_digest=source_digest,
        )
