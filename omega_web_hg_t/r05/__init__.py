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
    "AttributionPolicy",
    "BUILTIN_POLICIES",
    "CompiledPolicy",
    "GateDecision",
    "GateViolation",
    "PolicyCompilationError",
    "PolicyGate",
    "PolicyProfile",
    "PolicyRegistry",
    "PolicyViolation",
    "RequestContext",
    "RequestRatePolicy",
    "RequiredIdentityPolicy",
    "RetentionPolicy",
    "ReviewPolicy",
    "StorageDecisionRecord",
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
