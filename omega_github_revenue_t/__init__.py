"""Ω-GITHUB-REVENUE-T∞ / OAKSponsorOS-T.

Evidence-bearing, privacy-safe primitives for turning GitHub research artifacts
into reviewable sponsorship, service, product, licensing, and validation candidates.
"""

from .atlas import AtlasEdge, AtlasNode, build_revenue_atlas, default_system_atlas
from .authorization import (
    AuditAuthorization,
    AuthorizationError,
    Operation,
    require_local_repository_match,
)
from .campaign import (
    CampaignConfig,
    CampaignReceipt,
    run_campaign,
    stable_shard,
    synthetic_artifacts,
)
from .conversion import (
    BetaPosterior,
    FunnelSnapshot,
    analyze_funnel,
    posterior,
    recommend_funnel_action,
)
from .engine import (
    allocate_capital,
    assess_sponsor_tier,
    compile_offer,
    decide_experiment,
    evaluate_artifact,
    stream_frontier,
)
from .ledger import AppendOnlyLedger, SensitiveDataError
from .models import (
    Artifact,
    DisclosureClass,
    Evidence,
    Experiment,
    ExperimentDecision,
    OAKStatus,
    Offer,
    RevenueEvent,
    RevenuePath,
    SponsorTier,
)
from .oakgate import OAKGateRunReceipt, run_oakgate
from .portfolio import (
    PortfolioCandidate,
    allocate_portfolio,
    dependency_order,
    dominates,
    pareto_front,
)
from .pricing import DeliveryEstimate, PriceEnvelope, delivery_economics, price_envelope
from .privacy import (
    PrivacyFinding,
    redact_text,
    reject_secret_values,
    scan_payload,
    scan_text,
    summarize_findings,
)
from .profile import (
    ProjectCard,
    SponsorProfile,
    render_profile_readme,
    render_sponsor_tiers,
    validate_profile,
    write_profile_bundle,
)
from .reconciliation import ProviderEvent, reconcile_events
from .repository_audit import (
    AuditFinding,
    AuditPolicy,
    RepositoryAuditReport,
    audit_repository,
    render_markdown,
    write_report_bundle,
)
from .store import CampaignStore
from .transparency import (
    EvidenceManifest,
    ManifestEntry,
    build_manifest,
    digest_file,
    digest_payload,
    merkle_proof,
    merkle_root,
    verify_merkle_proof,
)

__all__ = [
    "allocate_capital",
    "assess_sponsor_tier",
    "compile_offer",
    "decide_experiment",
    "evaluate_artifact",
    "stream_frontier",
    "AppendOnlyLedger",
    "SensitiveDataError",
    "Artifact",
    "DisclosureClass",
    "Evidence",
    "Experiment",
    "ExperimentDecision",
    "OAKStatus",
    "Offer",
    "RevenueEvent",
    "RevenuePath",
    "SponsorTier",
    "AuditAuthorization",
    "AuthorizationError",
    "Operation",
    "require_local_repository_match",
    "AuditPolicy",
    "AuditFinding",
    "RepositoryAuditReport",
    "audit_repository",
    "render_markdown",
    "write_report_bundle",
    "PrivacyFinding",
    "scan_text",
    "scan_payload",
    "redact_text",
    "reject_secret_values",
    "summarize_findings",
    "ManifestEntry",
    "EvidenceManifest",
    "digest_payload",
    "digest_file",
    "merkle_root",
    "merkle_proof",
    "verify_merkle_proof",
    "build_manifest",
    "CampaignStore",
    "CampaignConfig",
    "CampaignReceipt",
    "run_campaign",
    "stable_shard",
    "synthetic_artifacts",
    "BetaPosterior",
    "FunnelSnapshot",
    "posterior",
    "analyze_funnel",
    "recommend_funnel_action",
    "ProviderEvent",
    "reconcile_events",
    "DeliveryEstimate",
    "PriceEnvelope",
    "price_envelope",
    "delivery_economics",
    "ProjectCard",
    "SponsorProfile",
    "validate_profile",
    "render_profile_readme",
    "render_sponsor_tiers",
    "write_profile_bundle",
    "PortfolioCandidate",
    "dominates",
    "pareto_front",
    "dependency_order",
    "allocate_portfolio",
    "AtlasNode",
    "AtlasEdge",
    "build_revenue_atlas",
    "default_system_atlas",
    "OAKGateRunReceipt",
    "run_oakgate",
]

__version__ = "0.2.0"
