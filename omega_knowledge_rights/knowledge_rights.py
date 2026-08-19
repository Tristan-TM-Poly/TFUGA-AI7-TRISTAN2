"""Ω Knowledge Rights Kernel R0.2.

Technical governance prototype only. Policy != Law.
No external action is performed by this module.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Iterable, Mapping

OPERATIONS = {
    "READ", "COPY", "DERIVE", "SUMMARIZE", "SIMULATE", "TRAIN",
    "BENCHMARK", "PUBLISH", "PATENT", "LICENSE", "SELL", "TRANSFER",
    "ARCHIVE", "DELETE", "PROVE", "AGGREGATE", "EXPORT",
}
OUTCOMES = {"ALLOW", "ESCALATE", "DENY"}
REQUIRED_GENOME_FIELDS = {
    "asset_id", "policy_version", "origin", "custodian", "classification",
    "privacy_status", "ip_status", "publication_status", "allowed_purposes",
    "allowed_operations", "forbidden_operations", "release_triggers",
    "protected_disclosure_kernel", "evidence_refs",
}


class PolicyError(ValueError):
    """Raised when an input cannot be evaluated safely."""


@dataclass(frozen=True)
class Request:
    actor: str
    asset_id: str
    purpose: str
    operation: str
    timestamp: str
    context: str = "standard"


@dataclass(frozen=True)
class Decision:
    outcome: str
    reasons: tuple[str, ...]
    conflict_rule_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _parse_time(value: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise PolicyError(f"invalid timestamp: {value!r}") from exc
    if dt.tzinfo is None:
        raise PolicyError("timestamp must include timezone")
    return dt.astimezone(timezone.utc)


def validate_genome(genome: Mapping[str, Any]) -> None:
    missing = sorted(REQUIRED_GENOME_FIELDS - set(genome))
    if missing:
        raise PolicyError(f"missing genome fields: {', '.join(missing)}")
    if not isinstance(genome["asset_id"], str) or not genome["asset_id"].strip():
        raise PolicyError("asset_id must be a non-empty string")
    if not isinstance(genome["allowed_purposes"], list):
        raise PolicyError("allowed_purposes must be a list")
    for key in ("allowed_operations", "forbidden_operations"):
        values = genome[key]
        if not isinstance(values, list):
            raise PolicyError(f"{key} must be a list")
        unknown = sorted(set(values) - OPERATIONS)
        if unknown:
            raise PolicyError(f"unknown operations in {key}: {unknown}")
    overlap = set(genome["allowed_operations"]) & set(genome["forbidden_operations"])
    if overlap:
        raise PolicyError(f"base policy directly conflicts on: {sorted(overlap)}")
    pdk = genome["protected_disclosure_kernel"]
    if not isinstance(pdk, Mapping) or not isinstance(pdk.get("enabled"), bool):
        raise PolicyError("protected_disclosure_kernel must define boolean enabled")
    if not isinstance(pdk.get("contexts"), list):
        raise PolicyError("protected_disclosure_kernel.contexts must be a list")
    if genome.get("expires_at") is not None:
        _parse_time(genome["expires_at"])
    for rule in genome.get("rules", []):
        if rule.get("effect") not in {"ALLOW", "DENY"}:
            raise PolicyError(f"invalid rule effect for {rule.get('rule_id')!r}")
        if not rule.get("rule_id"):
            raise PolicyError("every rule needs rule_id")
        operations = rule.get("operations")
        if not isinstance(operations, list) or not operations:
            raise PolicyError(f"rule {rule['rule_id']} needs operations")
        unknown = sorted(set(operations) - OPERATIONS)
        if unknown:
            raise PolicyError(f"unknown operations in rule {rule['rule_id']}: {unknown}")


def validate_request(request: Request) -> None:
    if not request.actor.strip() or not request.asset_id.strip() or not request.purpose.strip():
        raise PolicyError("actor, asset_id and purpose must be non-empty")
    if request.operation not in OPERATIONS:
        raise PolicyError(f"unknown operation: {request.operation}")
    _parse_time(request.timestamp)


def _scope_matches(rule: Mapping[str, Any], request: Request) -> bool:
    actors = rule.get("actors") or []
    purposes = rule.get("purposes") or []
    return (
        request.operation in set(rule.get("operations", []))
        and (not actors or request.actor in actors)
        and (not purposes or request.purpose in purposes)
    )


def applicable_rules(genome: Mapping[str, Any], request: Request) -> list[Mapping[str, Any]]:
    return [rule for rule in genome.get("rules", []) if _scope_matches(rule, request)]


def conflict_rule_ids(genome: Mapping[str, Any], request: Request) -> tuple[str, ...]:
    rules = applicable_rules(genome, request)
    effects = {rule["effect"] for rule in rules}
    if effects == {"ALLOW", "DENY"}:
        return tuple(sorted(rule["rule_id"] for rule in rules))
    return ()


def evaluate(genome: Mapping[str, Any], request: Request) -> Decision:
    """Evaluate one request with explicit, fail-closed semantics."""
    validate_genome(genome)
    validate_request(request)

    if request.asset_id != genome["asset_id"]:
        return Decision("DENY", ("asset_mismatch",))

    conflicts = conflict_rule_ids(genome, request)
    if conflicts:
        return Decision("DENY", ("policy_conflict_fail_closed",), conflicts)

    expires_at = genome.get("expires_at")
    if expires_at and _parse_time(request.timestamp) >= _parse_time(expires_at):
        return Decision("DENY", ("permission_expired",))

    pdk = genome["protected_disclosure_kernel"]
    if pdk["enabled"] and request.context in set(pdk["contexts"]):
        return Decision(
            "ESCALATE",
            ("protected_or_legally_required_disclosure_path", "qualified_review_required"),
        )

    if request.purpose not in set(genome["allowed_purposes"]):
        return Decision("DENY", ("purpose_not_explicitly_allowed",))

    if request.operation in set(genome["forbidden_operations"]):
        return Decision("DENY", ("operation_explicitly_forbidden",))

    rules = applicable_rules(genome, request)
    if any(rule["effect"] == "DENY" for rule in rules):
        return Decision("DENY", ("scoped_rule_denies",))
    if rules and any(rule["effect"] == "ALLOW" for rule in rules):
        return Decision("ALLOW", ("scoped_rule_allows",))

    if request.operation not in set(genome["allowed_operations"]):
        return Decision("DENY", ("operation_not_explicitly_allowed",))

    return Decision("ALLOW", ("base_policy_allows",))


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_manifest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def make_disclosure_receipt(
    genome: Mapping[str, Any],
    request: Request,
    disclosed_manifest: Any,
    *,
    decided_at: str | None = None,
) -> dict[str, Any]:
    decision = evaluate(genome, request)
    if decision.outcome != "ALLOW":
        raise PolicyError(f"receipt refused for non-ALLOW decision: {decision.outcome}")
    timestamp = decided_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    _parse_time(timestamp)
    receipt = {
        "schema": "OMEGA-KNOWLEDGE-RIGHTS-DISCLOSURE-RECEIPT/0.2",
        "asset_id": request.asset_id,
        "actor": request.actor,
        "purpose": request.purpose,
        "operation": request.operation,
        "policy_version": genome["policy_version"],
        "decided_at": timestamp,
        "manifest_sha256": sha256_manifest(disclosed_manifest),
        "decision": decision.to_dict(),
        "oak_invariants": [
            "Generated != Verified",
            "Policy != Law",
            "Receipt != LegalProof",
            "CanSee != CanExport != CanPublish",
            "ReadPermission != AITrainingPermission",
        ],
    }
    receipt["receipt_sha256"] = sha256_manifest(receipt)
    return receipt


def evaluate_many(genome: Mapping[str, Any], requests: Iterable[Request]) -> list[Decision]:
    return [evaluate(genome, request) for request in requests]
