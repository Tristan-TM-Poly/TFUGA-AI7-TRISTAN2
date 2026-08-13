from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Iterable
import json

SCHEMA_VERSION = "0.1.0"
AUTHORITIES = ("read", "draft", "write", "irreversible")
HEALTH_FACTORS = {
    "PASS": 1.00,
    "UNKNOWN": 0.90,
    "DEGRADED": 0.60,
    "FAIL": 0.00,
}


def _stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_digest(value: Any) -> str:
    return sha256(_stable_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Capability:
    capability_id: str
    domains: tuple[str, ...]
    consumes: tuple[str, ...]
    produces: tuple[str, ...]
    authority: str = "read"
    quality: float = 0.5
    information_gain: float = 0.5
    verifiability: float = 0.5
    reuse: float = 0.5
    cost: float = 0.5
    latency: float = 0.5
    risk: float = 0.5
    alternatives: tuple[str, ...] = ()
    failure_modes: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Capability":
        return cls(
            capability_id=str(payload["id"]),
            domains=tuple(map(str, payload.get("domains", []))),
            consumes=tuple(map(str, payload.get("consumes", []))),
            produces=tuple(map(str, payload.get("produces", []))),
            authority=str(payload.get("authority", "read")),
            quality=float(payload.get("quality", 0.5)),
            information_gain=float(payload.get("information_gain", 0.5)),
            verifiability=float(payload.get("verifiability", 0.5)),
            reuse=float(payload.get("reuse", 0.5)),
            cost=float(payload.get("cost", 0.5)),
            latency=float(payload.get("latency", 0.5)),
            risk=float(payload.get("risk", 0.5)),
            alternatives=tuple(map(str, payload.get("alternatives", []))),
            failure_modes=tuple(map(str, payload.get("failure_modes", []))),
        )

    def utility(self) -> float:
        score = (
            0.24 * self.quality
            + 0.20 * self.information_gain
            + 0.18 * self.verifiability
            + 0.16 * self.reuse
            - 0.08 * self.cost
            - 0.06 * self.latency
            - 0.08 * self.risk
        )
        return round(score, 6)


@dataclass(frozen=True)
class Intent:
    intent_id: str
    available_inputs: tuple[str, ...]
    required_outputs: tuple[str, ...]
    domains: tuple[str, ...] = ()
    allow_mutation: bool = False
    allow_irreversible: bool = False
    max_steps: int = 32

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Intent":
        return cls(
            intent_id=str(payload["intent_id"]),
            available_inputs=tuple(map(str, payload.get("available_inputs", []))),
            required_outputs=tuple(map(str, payload.get("required_outputs", []))),
            domains=tuple(map(str, payload.get("domains", []))),
            allow_mutation=bool(payload.get("allow_mutation", False)),
            allow_irreversible=bool(payload.get("allow_irreversible", False)),
            max_steps=int(payload.get("max_steps", 32)),
        )


def load_registry(payload: dict[str, Any]) -> tuple[Capability, ...]:
    return tuple(Capability.from_dict(item) for item in payload.get("capabilities", []))


def health_status(health: dict[str, Any] | None, capability_id: str) -> str:
    if not health:
        return "UNKNOWN"
    raw = health.get(capability_id, "UNKNOWN")
    if isinstance(raw, dict):
        raw = raw.get("status", "UNKNOWN")
    status = str(raw).upper()
    return status if status in HEALTH_FACTORS else "UNKNOWN"


def effective_utility(capability: Capability, health: dict[str, Any] | None = None) -> float:
    return round(capability.utility() * HEALTH_FACTORS[health_status(health, capability.capability_id)], 6)


def authority_allowed(capability: Capability, intent: Intent) -> bool:
    if capability.authority in {"read", "draft"}:
        return True
    if capability.authority == "write":
        return intent.allow_mutation
    if capability.authority == "irreversible":
        return intent.allow_mutation and intent.allow_irreversible
    return False


def validate_registry(registry: Iterable[Capability]) -> dict[str, Any]:
    caps = tuple(registry)
    errors: list[str] = []
    warnings: list[str] = []
    ids = [cap.capability_id for cap in caps]
    duplicate_ids = sorted({cid for cid in ids if ids.count(cid) > 1})
    if duplicate_ids:
        errors.append(f"duplicate capability ids: {duplicate_ids}")
    known = set(ids)
    for cap in caps:
        if cap.authority not in AUTHORITIES:
            errors.append(f"{cap.capability_id}: invalid authority {cap.authority!r}")
        for field in ("quality", "information_gain", "verifiability", "reuse", "cost", "latency", "risk"):
            value = float(getattr(cap, field))
            if not 0.0 <= value <= 1.0:
                errors.append(f"{cap.capability_id}: {field} outside [0,1]")
        missing_alts = sorted(set(cap.alternatives) - known)
        if missing_alts:
            errors.append(f"{cap.capability_id}: unknown alternatives {missing_alts}")
        if not cap.produces:
            warnings.append(f"{cap.capability_id}: produces nothing")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "capability_count": len(caps),
    }


class PlanError(RuntimeError):
    pass


def plan(
    registry: Iterable[Capability],
    intent: Intent,
    health: dict[str, Any] | None = None,
) -> dict[str, Any]:
    caps = tuple(registry)
    validation = validate_registry(caps)
    if validation["status"] != "PASS":
        raise PlanError("; ".join(validation["errors"]))

    available = set(intent.available_inputs)
    selected: list[Capability] = []
    selected_ids: set[str] = set()
    visiting_tokens: set[str] = set()
    domains = set(intent.domains)

    def candidate_score(cap: Capability) -> tuple[float, str]:
        return (effective_utility(cap, health), cap.capability_id)

    def compatible(cap: Capability) -> bool:
        if not authority_allowed(cap, intent):
            return False
        if health_status(health, cap.capability_id) == "FAIL":
            return False
        if domains and cap.domains and not (domains & set(cap.domains)):
            return False
        return True

    def ensure_token(token: str) -> bool:
        if token in available:
            return True
        if token in visiting_tokens:
            return False
        visiting_tokens.add(token)
        try:
            candidates = [cap for cap in caps if token in cap.produces and compatible(cap)]
            candidates.sort(key=candidate_score, reverse=True)
            for cap in candidates:
                snapshot_available = set(available)
                snapshot_len = len(selected)
                snapshot_ids = set(selected_ids)
                if all(ensure_token(dep) for dep in cap.consumes):
                    if cap.capability_id not in selected_ids:
                        selected.append(cap)
                        selected_ids.add(cap.capability_id)
                        available.update(cap.produces)
                    return token in available
                available.clear()
                available.update(snapshot_available)
                del selected[snapshot_len:]
                selected_ids.clear()
                selected_ids.update(snapshot_ids)
            return False
        finally:
            visiting_tokens.remove(token)

    unresolved = [token for token in intent.required_outputs if not ensure_token(token)]
    if len(selected) > intent.max_steps:
        raise PlanError(f"plan exceeds max_steps={intent.max_steps}")

    steps = []
    for index, cap in enumerate(selected, start=1):
        steps.append(
            {
                "order": index,
                "capability_id": cap.capability_id,
                "authority": cap.authority,
                "consumes": list(cap.consumes),
                "produces": list(cap.produces),
                "health": health_status(health, cap.capability_id),
                "base_utility": cap.utility(),
                "effective_utility": effective_utility(cap, health),
            }
        )

    payload = {
        "schema_version": SCHEMA_VERSION,
        "intent_id": intent.intent_id,
        "mutation_allowed": intent.allow_mutation,
        "irreversible_allowed": intent.allow_irreversible,
        "available_inputs": list(intent.available_inputs),
        "required_outputs": list(intent.required_outputs),
        "steps": steps,
        "covered_outputs": [x for x in intent.required_outputs if x not in unresolved],
        "unresolved_outputs": unresolved,
        "status": "READY" if not unresolved else "HOLD",
    }
    payload["fingerprint"] = stable_digest(payload)
    return payload


def suggest_fallback(
    registry: Iterable[Capability],
    capability_id: str,
    health: dict[str, Any] | None = None,
) -> dict[str, Any]:
    caps = {cap.capability_id: cap for cap in registry}
    source = caps.get(capability_id)
    if source is None:
        raise KeyError(capability_id)
    candidates = [
        caps[alt] for alt in source.alternatives
        if alt in caps and health_status(health, alt) != "FAIL"
    ]
    candidates.sort(key=lambda cap: (effective_utility(cap, health), cap.capability_id), reverse=True)
    chosen = candidates[0] if candidates else None
    return {
        "capability_id": capability_id,
        "status": health_status(health, capability_id),
        "fallback": chosen.capability_id if chosen else None,
        "fallback_health": health_status(health, chosen.capability_id) if chosen else None,
        "fallback_effective_utility": effective_utility(chosen, health) if chosen else None,
    }


def make_evidence_receipt(
    plan_payload: dict[str, Any],
    *,
    candidate_sha: str | None,
    evidence_sha: str | None,
    observations: list[dict[str, Any]] | None = None,
    sources: list[str] | None = None,
) -> dict[str, Any]:
    fresh = bool(candidate_sha and evidence_sha and candidate_sha == evidence_sha)
    status = "PASS" if plan_payload.get("status") == "READY" and fresh else "HOLD"
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "intent_id": plan_payload.get("intent_id"),
        "plan_fingerprint": plan_payload.get("fingerprint"),
        "candidate_sha": candidate_sha,
        "evidence_sha": evidence_sha,
        "fresh": fresh,
        "sources": sources or [],
        "observations": observations or [],
        "unknowns": [] if fresh else ["evidence does not match the candidate commit SHA"],
        "oak": {
            "status": status,
            "boundary": "PASS certifies plan coverage and SHA freshness only; it does not certify semantic truth or external success.",
        },
    }
    receipt["fingerprint"] = stable_digest(receipt)
    return receipt


def outcome_record(
    capability_id: str,
    outcome: str,
    *,
    symptom: str | None = None,
    recovery_chain: list[str] | None = None,
) -> dict[str, Any]:
    normalized = outcome.upper()
    if normalized not in {"SUCCESS", "FAILURE", "DEGRADED"}:
        raise ValueError("outcome must be SUCCESS, FAILURE, or DEGRADED")
    record = {
        "schema_version": SCHEMA_VERSION,
        "capability_id": capability_id,
        "outcome": normalized,
        "memory": "M+" if normalized == "SUCCESS" else "M-",
        "symptom": symptom,
        "recovery_chain": recovery_chain or [],
    }
    record["fingerprint"] = stable_digest(record)
    return record
