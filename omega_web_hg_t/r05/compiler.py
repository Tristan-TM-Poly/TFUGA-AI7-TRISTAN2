"""Deterministic policy compiler for Ω-WEB-HG-T∞ R0.5."""
from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta
import json
from pathlib import Path
from typing import Any, Mapping

from .models import CompiledPolicy, PolicyProfile, canonical_json


class PolicyCompilationError(ValueError):
    """Raised when a policy cannot be compiled without unsafe guessing."""


def _as_date(value: str | date | None) -> date:
    if value is None:
        return date.today()
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _review_state(profile: PolicyProfile, as_of: date) -> tuple[str, tuple[str, ...]]:
    reasons: list[str] = []
    if profile.policy_status == "expired":
        return "fail", ("policy_profile_expired",)
    if profile.policy_status in {"ambiguous", "human_review_required"}:
        reasons.append(f"policy_status_{profile.policy_status}")
    elif profile.policy_status == "inferred":
        reasons.append("policy_contains_inferred_rules")

    observed = date.fromisoformat(profile.policy_observed_at)
    next_review = (
        date.fromisoformat(profile.review.next_review_at)
        if profile.review.next_review_at
        else observed + timedelta(days=profile.review.review_after_days)
    )
    if as_of > next_review:
        reasons.append("policy_review_overdue")
    if not profile.policy_url:
        reasons.append("policy_url_missing")
    if not profile.allowed_routes:
        return "fail", tuple(reasons + ["no_allowed_route"])
    if set(profile.allowed_content).intersection(profile.forbidden_content):
        return "fail", tuple(reasons + ["content_classification_conflict"])
    if reasons:
        return "human_review", tuple(sorted(set(reasons)))
    return "pass", ()


def compile_policy(profile: PolicyProfile, *, as_of: str | date | None = None) -> CompiledPolicy:
    """Compile one evidence-backed profile into a deterministic technical gate.

    The result is fail-closed. A profile marked ambiguous, inferred, expired or
    overdue never silently becomes executable permission.
    """
    evaluated = _as_date(as_of)
    review_status, review_reasons = _review_state(profile, evaluated)
    return CompiledPolicy(
        source_id=profile.source_id,
        allowed_routes=tuple(sorted(profile.allowed_routes)),
        allowed_content=tuple(sorted(profile.allowed_content)),
        allowed_fields=tuple(sorted(profile.allowed_fields)),
        forbidden_content=tuple(sorted(profile.forbidden_content)),
        forbidden_fields=tuple(sorted(profile.forbidden_fields)),
        retention_rules={
            "raw_response": profile.retention.raw_response,
            "normalized_metadata": profile.retention.normalized_metadata,
            "maximum_days": profile.retention.maximum_days,
            "encrypted_at_rest": profile.retention.encrypted_at_rest,
        },
        rate_rules={
            "recommended_rps": profile.request_rate.recommended_rps,
            "maximum_rps": profile.request_rate.maximum_rps,
            "burst": profile.request_rate.burst,
            "retry_after_required": profile.request_rate.retry_after_required,
        },
        identity_rules={
            "user_agent_required": profile.required_identity.user_agent_required,
            "contact_email": profile.required_identity.contact_email,
        },
        attribution_rules={
            "required": profile.attribution.required,
            "required_fields": tuple(sorted(profile.attribution.required_fields)),
        },
        required_environment=tuple(sorted(profile.required_environment)),
        enforcement_mode=profile.enforcement_mode,
        review_status=review_status,
        review_reasons=review_reasons,
        policy_url=profile.policy_url,
        policy_observed_at=profile.policy_observed_at,
        evaluated_as_of=evaluated.isoformat(),
        source_profile_digest=profile.digest,
    )


def compile_mapping(value: Mapping[str, Any], *, as_of: str | date | None = None) -> CompiledPolicy:
    return compile_policy(PolicyProfile.from_mapping(value), as_of=as_of)


def load_profile(path: str | Path) -> PolicyProfile:
    file_path = Path(path)
    if file_path.suffix.lower() not in {".json", ".jsonld"}:
        raise PolicyCompilationError(
            "R0.5 accepts canonical JSON profiles. Convert YAML to JSON before compilation "
            "so parsing semantics remain deterministic and dependency-free."
        )
    value = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise PolicyCompilationError("policy profile must be a JSON object")
    return PolicyProfile.from_mapping(value)


def write_profile(profile: PolicyProfile, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(profile.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def write_compiled(policy: CompiledPolicy, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(policy.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def compare_compiled_policies(old: CompiledPolicy, new: CompiledPolicy) -> dict[str, Any]:
    """Return an explicit policy drift report suitable for CI and M-minus."""
    old_payload = old.to_dict(include_digest=False)
    new_payload = new.to_dict(include_digest=False)
    ignored = {"evaluated_as_of", "review_status", "review_reasons"}
    changes: dict[str, dict[str, Any]] = {}
    for key in sorted(set(old_payload).union(new_payload) - ignored):
        if old_payload.get(key) != new_payload.get(key):
            changes[key] = {"before": old_payload.get(key), "after": new_payload.get(key)}

    old_forbidden = set(old.forbidden_fields)
    new_forbidden = set(new.forbidden_fields)
    old_routes = set(old.allowed_routes)
    new_routes = set(new.allowed_routes)
    old_required_env = set(old.required_environment)
    new_required_env = set(new.required_environment)
    risk_flags: list[str] = []
    if old_forbidden - new_forbidden:
        risk_flags.append("forbidden_fields_relaxed")
    if new_routes - old_routes:
        risk_flags.append("new_routes_enabled")
    if old_required_env - new_required_env:
        risk_flags.append("environment_requirement_relaxed")
    if old.retention_rules.get("raw_response") == "forbidden" and new.retention_rules.get("raw_response") != "forbidden":
        risk_flags.append("raw_response_retention_relaxed")
    if old.review_status == "pass" and new.review_status != "pass":
        risk_flags.append("review_status_degraded")

    return {
        "schema": "omega-web-hg-policy-drift/1.0",
        "source_id": new.source_id,
        "old_policy_digest": old.policy_digest,
        "new_policy_digest": new.policy_digest,
        "changed": bool(changes),
        "changes": changes,
        "risk_flags": sorted(risk_flags),
        "requires_human_review": bool(risk_flags) or new.review_status != "pass",
    }


def normalized_compilation(profile: PolicyProfile, *, as_of: str | date | None = None) -> str:
    """Canonical compiled representation used by deterministic regression tests."""
    return canonical_json(compile_policy(profile, as_of=as_of).to_dict())


def with_review_date(profile: PolicyProfile, next_review_at: str) -> PolicyProfile:
    """Convenience helper for controlled profile updates."""
    return replace(profile, review=replace(profile.review, next_review_at=next_review_at))
