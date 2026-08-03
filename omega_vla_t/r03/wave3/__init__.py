"""Ω-VLA-T∞³ Wave 3 Identity Factory."""
from .assumptions import Assumption, AssumptionKind, audit_assumptions
from .campaign import CampaignConfig, CampaignReport, run_campaign
from .catalog import SCHEMAS, catalog_manifest, schema_at_dimension, schema_by_id
from .compilers import CompiledTarget, compile_property_test, compile_smtlib_counterexample
from .dependency import DependencyAudit, IdentityDependencyGraph
from .expressions import ExprError, ExprKind, MatrixExpr, relative_residual
from .factory import instantiate, mutate_assumptions, mutate_schema
from .falsify import generate_environment, test_identity
from .frontier import IdentityFrontierCodec
from .models import (
    Counterexample, EvidenceState, IdentityAddress, IdentityInstance,
    IdentitySchema, IdentityTestReport,
)
from .oak import Wave3OAKReport, audit_wave3

__all__ = [
    "Assumption", "AssumptionKind", "CampaignConfig", "CampaignReport",
    "CompiledTarget", "Counterexample", "DependencyAudit", "EvidenceState",
    "ExprError", "ExprKind", "IdentityAddress", "IdentityDependencyGraph",
    "IdentityFrontierCodec", "IdentityInstance", "IdentitySchema",
    "IdentityTestReport", "MatrixExpr", "SCHEMAS", "Wave3OAKReport",
    "audit_assumptions", "audit_wave3", "catalog_manifest",
    "compile_property_test", "compile_smtlib_counterexample",
    "generate_environment", "instantiate", "mutate_assumptions",
    "mutate_schema", "relative_residual", "run_campaign",
    "schema_at_dimension", "schema_by_id", "test_identity",
]
