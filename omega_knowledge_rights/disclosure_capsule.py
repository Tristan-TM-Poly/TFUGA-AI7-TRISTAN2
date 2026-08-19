"""Deterministic field-level DisclosureCapsules for Ω Knowledge Rights R0.3.

This module implements explicit allow-list projection only. It does not claim
semantic redaction, de-identification, legal privilege, or secure sandboxing.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from .knowledge_rights import PolicyError, Request, canonical_json, evaluate, sha256_manifest


class DisclosureCapsuleError(PolicyError):
    """Raised when a disclosure capsule cannot be compiled safely."""


def _string_list(value: Any, *, name: str, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list):
        raise DisclosureCapsuleError(f"{name} must be a list")
    if not allow_empty and not value:
        raise DisclosureCapsuleError(f"{name} must not be empty")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise DisclosureCapsuleError(f"{name} must contain non-empty strings")
    if len(value) != len(set(value)):
        raise DisclosureCapsuleError(f"{name} must not contain duplicates")
    return value


def validate_capsule_spec(spec: Mapping[str, Any]) -> None:
    required = {"capsule_id", "asset_id", "operation", "include_fields", "required_fields"}
    missing = sorted(required - set(spec))
    if missing:
        raise DisclosureCapsuleError(f"missing capsule fields: {', '.join(missing)}")
    for key in ("capsule_id", "asset_id", "operation"):
        if not isinstance(spec[key], str) or not spec[key].strip():
            raise DisclosureCapsuleError(f"{key} must be a non-empty string")

    include = set(_string_list(spec["include_fields"], name="include_fields", allow_empty=False))
    required_fields = set(_string_list(spec["required_fields"], name="required_fields"))
    exclude = set(_string_list(spec.get("exclude_fields", []), name="exclude_fields"))
    actors = _string_list(spec.get("actors", []), name="actors")
    purposes = _string_list(spec.get("purposes", []), name="purposes")

    if not required_fields <= include:
        raise DisclosureCapsuleError("required_fields must be a subset of include_fields")
    overlap = include & exclude
    if overlap:
        raise DisclosureCapsuleError(f"include_fields conflicts with exclude_fields: {sorted(overlap)}")
    if actors and any(not actor.strip() for actor in actors):
        raise DisclosureCapsuleError("actors contains an empty value")
    if purposes and any(not purpose.strip() for purpose in purposes):
        raise DisclosureCapsuleError("purposes contains an empty value")


def _scope_matches(spec: Mapping[str, Any], request: Request) -> None:
    if spec["asset_id"] != request.asset_id:
        raise DisclosureCapsuleError("capsule_asset_mismatch")
    if spec["operation"] != request.operation:
        raise DisclosureCapsuleError("capsule_operation_mismatch")
    actors = set(spec.get("actors", []))
    purposes = set(spec.get("purposes", []))
    if actors and request.actor not in actors:
        raise DisclosureCapsuleError("capsule_actor_not_allowed")
    if purposes and request.purpose not in purposes:
        raise DisclosureCapsuleError("capsule_purpose_not_allowed")


def compile_capsule(
    genome: Mapping[str, Any],
    request: Request,
    source_record: Mapping[str, Any],
    spec: Mapping[str, Any],
) -> dict[str, Any]:
    """Compile one deterministic top-level-field disclosure projection.

    Every field absent from ``include_fields`` is omitted. This is an explicit
    structural projection, not semantic redaction.
    """
    validate_capsule_spec(spec)
    decision = evaluate(genome, request)
    if decision.outcome != "ALLOW":
        raise DisclosureCapsuleError(f"capsule refused for decision: {decision.outcome}")
    _scope_matches(spec, request)
    if not isinstance(source_record, Mapping):
        raise DisclosureCapsuleError("source_record must be a mapping")

    include = list(spec["include_fields"])
    required_fields = set(spec["required_fields"])
    missing_required = sorted(required_fields - set(source_record))
    if missing_required:
        raise DisclosureCapsuleError(f"missing required source fields: {missing_required}")

    payload = {field: source_record[field] for field in include if field in source_record}
    disclosed_fields = sorted(payload)
    omitted_fields = sorted(set(source_record) - set(disclosed_fields))
    manifest = {
        "schema": "OMEGA-DISCLOSURE-CAPSULE/0.3",
        "capsule_id": spec["capsule_id"],
        "asset_id": request.asset_id,
        "actor": request.actor,
        "purpose": request.purpose,
        "operation": request.operation,
        "policy_version": genome["policy_version"],
        "disclosed_fields": disclosed_fields,
        "omitted_fields": omitted_fields,
        "payload_sha256": sha256_manifest(payload),
        "projection_semantics": "top_level_field_allowlist",
        "semantic_redaction_claimed": False,
    }
    manifest["manifest_sha256"] = sha256_manifest(manifest)
    return {"payload": payload, "manifest": manifest}


def validate_reconstruction_rules(rules: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    normalized = list(rules)
    seen: set[str] = set()
    for rule in normalized:
        rule_id = rule.get("rule_id")
        if not isinstance(rule_id, str) or not rule_id.strip():
            raise DisclosureCapsuleError("every reconstruction rule needs rule_id")
        if rule_id in seen:
            raise DisclosureCapsuleError(f"duplicate reconstruction rule: {rule_id}")
        seen.add(rule_id)
        _string_list(rule.get("required_fields"), name=f"{rule_id}.required_fields", allow_empty=False)
    return normalized


def _manifest_fields(manifest: Mapping[str, Any]) -> set[str]:
    fields = manifest.get("disclosed_fields")
    return set(_string_list(fields, name="manifest.disclosed_fields"))


def assess_cumulative_reconstruction(
    history_manifests: Iterable[Mapping[str, Any]],
    candidate_manifest: Mapping[str, Any],
    reconstruction_rules: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Detect explicit field-set reconstruction risks across disclosure history.

    A rule triggers only when every named required field has been disclosed.
    This is a deterministic structural benchmark, not a semantic inference model.
    """
    rules = validate_reconstruction_rules(reconstruction_rules)
    history_fields: set[str] = set()
    for manifest in history_manifests:
        history_fields |= _manifest_fields(manifest)
    candidate_fields = _manifest_fields(candidate_manifest)
    union_fields = history_fields | candidate_fields

    already_triggered: list[str] = []
    newly_triggered: list[str] = []
    for rule in rules:
        required = set(rule["required_fields"])
        before = required <= history_fields
        after = required <= union_fields
        if before:
            already_triggered.append(rule["rule_id"])
        elif after:
            newly_triggered.append(rule["rule_id"])

    result = {
        "schema": "OMEGA-RECONSTRUCTION-COURT/0.3",
        "history_fields": sorted(history_fields),
        "candidate_fields": sorted(candidate_fields),
        "union_fields": sorted(union_fields),
        "already_triggered_rule_ids": sorted(already_triggered),
        "newly_triggered_rule_ids": sorted(newly_triggered),
        "safe_to_add": not newly_triggered,
        "semantics": "explicit_field_set_only",
        "semantic_inference_claimed": False,
    }
    result["assessment_sha256"] = sha256_manifest(result)
    return result


def compile_capsule_with_reconstruction_gate(
    genome: Mapping[str, Any],
    request: Request,
    source_record: Mapping[str, Any],
    spec: Mapping[str, Any],
    *,
    history_manifests: Iterable[Mapping[str, Any]] = (),
    reconstruction_rules: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    compiled = compile_capsule(genome, request, source_record, spec)
    assessment = assess_cumulative_reconstruction(
        history_manifests,
        compiled["manifest"],
        reconstruction_rules,
    )
    if not assessment["safe_to_add"]:
        raise DisclosureCapsuleError(
            "cumulative_reconstruction_risk:" + ",".join(assessment["newly_triggered_rule_ids"])
        )
    return {**compiled, "reconstruction_assessment": assessment}


def capsule_fingerprint(compiled: Mapping[str, Any]) -> str:
    """Stable fingerprint for a compiled capsule object."""
    return sha256_manifest(canonical_json(compiled))
