"""Least-privilege policy kernel for executable capabilities."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Iterable

from .capabilities import CapabilitySpec


class Permission(str, Enum):
    PURE = "PURE"
    FILESYSTEM_READ = "FILESYSTEM_READ"
    FILESYSTEM_WRITE = "FILESYSTEM_WRITE"
    NETWORK_READ = "NETWORK_READ"
    GITHUB_READ = "GITHUB_READ"
    GITHUB_WRITE = "GITHUB_WRITE"
    EXTERNAL_ACTION = "EXTERNAL_ACTION"
    IP_SENSITIVE = "IP_SENSITIVE"


@dataclass(frozen=True, slots=True)
class PolicyContext:
    allowed: frozenset[str] = field(default_factory=lambda: frozenset({Permission.PURE.value}))
    approval_required: frozenset[str] = field(default_factory=lambda: frozenset({Permission.GITHUB_WRITE.value, Permission.EXTERNAL_ACTION.value, Permission.IP_SENSITIVE.value}))

    @classmethod
    def sandbox(cls, extra: Iterable[str] = ()) -> "PolicyContext":
        return cls(allowed=frozenset({Permission.PURE.value, *map(str, extra)}))


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    allowed: bool
    approval_required: bool
    missing_permissions: tuple[str, ...]
    approval_permissions: tuple[str, ...]
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PolicyKernel:
    def evaluate(self, capability: CapabilitySpec, context: PolicyContext | None = None) -> PolicyDecision:
        context = context or PolicyContext()
        requested = tuple(dict.fromkeys(capability.permissions or (Permission.PURE.value,)))
        missing = tuple(sorted(permission for permission in requested if permission not in context.allowed))
        approvals = tuple(sorted(permission for permission in requested if permission in context.approval_required))
        allowed = not missing
        approval_required = bool(approvals) and not all(p in context.allowed for p in approvals)
        if missing:
            reason = "Capability requests permissions not granted by the current execution context."
        elif approvals:
            reason = "Capability permission set is granted; sensitive permissions remain auditable."
        else:
            reason = "Capability fits the current least-privilege execution context."
        return PolicyDecision(allowed, approval_required, missing, approvals, reason)

    def require(self, capability: CapabilitySpec, context: PolicyContext | None = None) -> PolicyDecision:
        decision = self.evaluate(capability, context)
        if not decision.allowed:
            raise PermissionError(f"Capability {capability.id!r} blocked: {', '.join(decision.missing_permissions)}")
        return decision
