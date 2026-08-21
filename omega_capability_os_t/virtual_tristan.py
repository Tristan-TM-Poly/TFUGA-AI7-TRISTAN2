"""Virtual Tristan projections for Capability OS.

A Virtual Tristan is not an autonomous sovereign agent. It is an ephemeral,
role-scoped projection over existing Capability OS capabilities, bounded by
intent authority, evidence contracts, budgets, and explicit separation of
construction, falsification, verification, and promotion authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from omega_capability_os_t.core import Capability, Intent, authority_allowed, stable_digest

CORE_ROLES = (
    "mycelium",
    "architect",
    "engineer",
    "founder",
    "oak",
)

COUNTERPOWER_ROLES = (
    "falsifier",
    "reality",
    "historian",
    "compressor",
    "apoptosis",
    "collusion",
)


@dataclass(frozen=True)
class VirtualTristanSpec:
    tristan_id: str
    role: str
    capability_ids: tuple[str, ...]
    budget: float = 1.0
    authority: str = "read"
    ephemeral: bool = True
    evidence_contract: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.tristan_id.strip():
            raise ValueError("tristan_id must be non-empty")
        if not self.role.strip():
            raise ValueError("role must be non-empty")
        if self.budget <= 0:
            raise ValueError("budget must be > 0")


@dataclass(frozen=True)
class VirtualTristanPopulation:
    intent_id: str
    members: tuple[VirtualTristanSpec, ...]
    unresolved_roles: tuple[str, ...]
    decision: str
    blockers: tuple[str, ...]
    fingerprint: str
    oak_boundary: str = (
        "READY means a finite role population was compiled from supplied Capability OS capabilities under declared authority and budget. "
        "It does not prove intelligence, truth, independence, or external success; consensus is only a signal."
    )


def _compatible_capabilities(
    registry: Iterable[Capability], intent: Intent
) -> tuple[Capability, ...]:
    return tuple(cap for cap in registry if authority_allowed(cap, intent))


def compile_virtual_tristans(
    registry: Iterable[Capability],
    intent: Intent,
    *,
    required_roles: Iterable[str],
    role_capabilities: Mapping[str, Iterable[str]],
    max_population: int = 16,
    total_budget: float = 8.0,
) -> VirtualTristanPopulation:
    if max_population < 1:
        raise ValueError("max_population must be >= 1")
    if total_budget <= 0:
        raise ValueError("total_budget must be > 0")

    caps = {cap.capability_id: cap for cap in _compatible_capabilities(registry, intent)}
    members: list[VirtualTristanSpec] = []
    unresolved: list[str] = []
    blockers: list[str] = []
    seen_roles: set[str] = set()

    for raw_role in required_roles:
        role = str(raw_role).strip()
        if not role or role in seen_roles:
            continue
        seen_roles.add(role)
        requested = tuple(str(x) for x in role_capabilities.get(role, ()))
        usable = tuple(cid for cid in requested if cid in caps)
        if not usable:
            unresolved.append(role)
            continue
        member_authorities = {caps[cid].authority for cid in usable}
        authority = max(member_authorities, key=("read", "draft", "write", "irreversible").index)
        members.append(
            VirtualTristanSpec(
                tristan_id=f"vt:{role}",
                role=role,
                capability_ids=usable,
                budget=1.0,
                authority=authority,
                ephemeral=True,
                evidence_contract=("receipt", "residuals", "uncertainty"),
            )
        )

    if len(members) > max_population:
        blockers.append("population_budget_exceeded")
    if sum(member.budget for member in members) > total_budget:
        blockers.append("compute_budget_exceeded")
    if unresolved:
        blockers.append("required_role_unresolved")

    payload = {
        "intent_id": intent.intent_id,
        "members": [
            {
                "id": m.tristan_id,
                "role": m.role,
                "capability_ids": list(m.capability_ids),
                "budget": m.budget,
                "authority": m.authority,
                "ephemeral": m.ephemeral,
                "evidence_contract": list(m.evidence_contract),
            }
            for m in members
        ],
        "unresolved_roles": sorted(unresolved),
        "blockers": sorted(set(blockers)),
    }
    return VirtualTristanPopulation(
        intent.intent_id,
        tuple(members),
        tuple(sorted(unresolved)),
        "READY" if not blockers else "HOLD",
        tuple(sorted(set(blockers))),
        stable_digest(payload),
    )


def separation_gate(
    *,
    generator_id: str,
    falsifier_id: str,
    verifier_id: str,
    promotion_authority_id: str,
) -> dict[str, object]:
    identities = (generator_id, falsifier_id, verifier_id, promotion_authority_id)
    distinct = len(set(identities)) == len(identities)
    return {
        "decision": "PASS" if distinct else "HOLD",
        "independent_identities": distinct,
        "blockers": [] if distinct else ["role_authority_collapse"],
        "oak_boundary": "Distinct identities reduce explicit role collapse; they do not establish statistical, semantic, or source independence.",
    }


def apoptosis_candidates(
    contribution_by_tristan: Mapping[str, float], *, threshold: float = 0.0
) -> tuple[str, ...]:
    """Return members whose measured marginal contribution does not exceed threshold."""
    return tuple(sorted(
        tristan_id
        for tristan_id, contribution in contribution_by_tristan.items()
        if float(contribution) <= threshold
    ))
