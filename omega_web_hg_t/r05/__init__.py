"""Ω-WEB-HG-T∞ R0.5 — executable policy compiler and runtime gates."""

from .builtin_policies import BUILTIN_POLICIES, executable_policies, policy_by_id
from .compiler import (
    PolicyCompilationError,
    compare_compiled_policies,
    compile_mapping,
    compile_policy,
    load_profile,
    normalized_compilation,
    write_compiled,
    write_profile,
)
from .gate import PolicyGate, PolicyViolation, RequestContext
from .integration import (
    AdapterPolicyBindingError,
    AuthorizedRequest,
    GatedParseBatch,
    PolicyBoundAdapter,
    ROUTE_BY_SOURCE,
    audit_r04_bindings,
    bind_adapter,
    bind_all_r04_adapters,
)
from .models import (
    AttributionPolicy,
    CompiledPolicy,
    GateDecision,
    GateViolation,
    PolicyProfile,
    RequestRatePolicy,
    RequiredIdentityPolicy,
    RetentionPolicy,
    ReviewPolicy,
    StorageDecisionRecord,
)
from .registry import PolicyRegistry

__all__ = [
    "AdapterPolicyBindingError",
    "AttributionPolicy",
    "AuthorizedRequest",
    "BUILTIN_POLICIES",
    "CompiledPolicy",
    "GateDecision",
    "GateViolation",
    "GatedParseBatch",
    "PolicyBoundAdapter",
    "PolicyCompilationError",
    "PolicyGate",
    "PolicyProfile",
    "PolicyRegistry",
    "PolicyViolation",
    "ROUTE_BY_SOURCE",
    "RequestContext",
    "RequestRatePolicy",
    "RequiredIdentityPolicy",
    "RetentionPolicy",
    "ReviewPolicy",
    "StorageDecisionRecord",
    "audit_r04_bindings",
    "bind_adapter",
    "bind_all_r04_adapters",
    "compare_compiled_policies",
    "compile_mapping",
    "compile_policy",
    "executable_policies",
    "load_profile",
    "normalized_compilation",
    "policy_by_id",
    "write_compiled",
    "write_profile",
]
