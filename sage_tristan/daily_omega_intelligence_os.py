"""Daily Omega Intelligence OS compiler.

This layer converts a BriefingItem into a reusable SignalGenome++: a compact,
JSON-safe strategic object that connects source verification, claim separation,
evidence scoring, OAK review, canon routing, IP posture, prototype ladder,
revenue physics, v3 strategic risk ledgers, memory notes, and canon status.

It performs no network calls and creates no public issues.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from sage_tristan.daily_omega_briefing import BriefingItem, Source
from sage_tristan.daily_omega_router import route_item
from sage_tristan.daily_omega_supervisor import supervise_issue_spec

PROTOTYPE_HORIZONS = ("none", "15_min", "2_hour", "1_day", "1_week")
REVENUE_ROUTES = (
    "none",
    "service",
    "audit",
    "report",
    "template",
    "software",
    "dataset",
    "api",
    "grant",
    "consulting",
    "licensing",
    "course",
)
CANON_STATUS_LADDER = (
    "raw_signal",
    "imported_signal",
    "source_required",
    "source_verified",
    "oak_reviewed",
    "issue_candidate",
    "prototype_candidate",
    "prior_art_candidate",
    "revenue_candidate",
    "validated",
    "rejected",
    "canon_candidate",
    "canonized",
)


@dataclass(frozen=True)
class SourceLedgerEntry:
    """OAK-safe verification state for one source."""

    title: str
    source_type: str
    url_or_identifier: str
    source_quality: int
    verification_status: str
    residue: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "source_type": self.source_type,
            "url_or_identifier": self.url_or_identifier,
            "source_quality": self.source_quality,
            "verification_status": self.verification_status,
            "residue": self.residue,
        }


@dataclass(frozen=True)
class ClaimNode:
    """Separated claim node: fact, inference, or speculative extension."""

    claim_type: str
    text: str
    oak_status: str

    def to_dict(self) -> dict[str, str]:
        return {"claim_type": self.claim_type, "text": self.text, "oak_status": self.oak_status}


@dataclass(frozen=True)
class EvidenceMatrix:
    """Compact evidence matrix for one signal."""

    freshness: int
    source: int
    fit: int
    actionability: int
    ip: int
    revenue: int
    prototype: int
    risk: int
    residue: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "freshness": self.freshness,
            "source": self.source,
            "fit": self.fit,
            "actionability": self.actionability,
            "ip": self.ip,
            "revenue": self.revenue,
            "prototype": self.prototype,
            "risk": self.risk,
            "residue": self.residue,
        }


@dataclass(frozen=True)
class PrototypeLadder:
    """P0..P4 prototype ladder for a signal."""

    p0_15_min: str
    p1_2_hour: str
    p2_1_day: str
    p3_1_week: str
    p4_1_month: str

    def to_dict(self) -> dict[str, str]:
        return {
            "P0_15_min": self.p0_15_min,
            "P1_2_hour": self.p1_2_hour,
            "P2_1_day": self.p2_1_day,
            "P3_1_week": self.p3_1_week,
            "P4_1_month": self.p4_1_month,
        }


@dataclass(frozen=True)
class RevenuePhysics:
    """Revenue ladder from no monetization to company/spinout."""

    level: str
    routes: tuple[str, ...]
    first_experiment: str

    def to_dict(self) -> dict[str, Any]:
        return {"level": self.level, "routes": list(self.routes), "first_experiment": self.first_experiment}


@dataclass(frozen=True)
class AgentSecurityLedger:
    """Security posture for agentic or automation-related signals."""

    permission_scope: str
    human_approval_required: bool
    rollback_required: bool
    audit_logs_required: bool
    abuse_cases: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "permission_scope": self.permission_scope,
            "human_approval_required": self.human_approval_required,
            "rollback_required": self.rollback_required,
            "audit_logs_required": self.audit_logs_required,
            "abuse_cases": list(self.abuse_cases),
        }


@dataclass(frozen=True)
class ObservabilitySignal:
    """Metrics required to know whether a signal becomes operational value."""

    metrics: tuple[str, ...]
    required: bool
    first_metric_to_measure: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "metrics": list(self.metrics),
            "required": self.required,
            "first_metric_to_measure": self.first_metric_to_measure,
        }


@dataclass(frozen=True)
class FundingSignal:
    """Funding and business signal extracted from a briefing item."""

    routes: tuple[str, ...]
    strength: str
    first_action: str

    def to_dict(self) -> dict[str, Any]:
        return {"routes": list(self.routes), "strength": self.strength, "first_action": self.first_action}


@dataclass(frozen=True)
class InfrastructureDependency:
    """Hidden infrastructure dependencies behind an opportunity."""

    dependencies: tuple[str, ...]
    risk_level: str
    first_check: str

    def to_dict(self) -> dict[str, Any]:
        return {"dependencies": list(self.dependencies), "risk_level": self.risk_level, "first_check": self.first_check}


@dataclass(frozen=True)
class CriticalMaterialDependency:
    """Critical material dependencies for energy, photonics, compute, and hardware signals."""

    materials: tuple[str, ...]
    risk_level: str
    first_check: str

    def to_dict(self) -> dict[str, Any]:
        return {"materials": list(self.materials), "risk_level": self.risk_level, "first_check": self.first_check}


@dataclass(frozen=True)
class OakValidationRoute:
    """OAK checks required before promotion, publication, or productization."""

    checks: tuple[str, ...]
    blocking_check: str
    promotion_allowed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "checks": list(self.checks),
            "blocking_check": self.blocking_check,
            "promotion_allowed": self.promotion_allowed,
        }


@dataclass(frozen=True)
class SignalGenome:
    """Portable strategic genome for one Daily Omega signal."""

    title: str
    final_score: int
    canon_branches: tuple[str, ...]
    ip_classification: str
    issue_type: str
    supervision_mode: str
    prototype_horizon: str
    revenue_routes: tuple[str, ...]
    canon_status: str
    m_plus: str
    m_minus: str
    next_action: str
    source_ledger: tuple[SourceLedgerEntry, ...]
    claim_graph: tuple[ClaimNode, ...]
    evidence_matrix: EvidenceMatrix
    prototype_ladder: PrototypeLadder
    revenue_physics: RevenuePhysics
    agent_security_ledger: AgentSecurityLedger
    observability_signal: ObservabilitySignal
    funding_signal: FundingSignal
    ip_risk_level: str
    infrastructure_dependency: InfrastructureDependency
    critical_material_dependency: CriticalMaterialDependency
    oak_validation_route: OakValidationRoute

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "final_score": self.final_score,
            "canon_branches": list(self.canon_branches),
            "ip_classification": self.ip_classification,
            "issue_type": self.issue_type,
            "supervision_mode": self.supervision_mode,
            "prototype_horizon": self.prototype_horizon,
            "revenue_routes": list(self.revenue_routes),
            "canon_status": self.canon_status,
            "m_plus": self.m_plus,
            "m_minus": self.m_minus,
            "next_action": self.next_action,
            "source_ledger": [entry.to_dict() for entry in self.source_ledger],
            "claim_graph": [claim.to_dict() for claim in self.claim_graph],
            "evidence_matrix": self.evidence_matrix.to_dict(),
            "prototype_ladder": self.prototype_ladder.to_dict(),
            "revenue_physics": self.revenue_physics.to_dict(),
            "agent_security_ledger": self.agent_security_ledger.to_dict(),
            "observability_signal": self.observability_signal.to_dict(),
            "funding_signal": self.funding_signal.to_dict(),
            "ip_risk_level": self.ip_risk_level,
            "infrastructure_dependency": self.infrastructure_dependency.to_dict(),
            "critical_material_dependency": self.critical_material_dependency.to_dict(),
            "oak_validation_route": self.oak_validation_route.to_dict(),
        }


def _bounded_score(value: int) -> int:
    return max(0, min(5, int(value)))


def _text_blob(item: BriefingItem) -> str:
    return " ".join(
        [
            item.title,
            item.why_it_matters,
            item.actionable_opportunity,
            item.business_funding_signal,
            item.ip_signal,
            item.next_action,
            " ".join(item.signal_type),
            item.oak_check.risk,
            item.oak_check.falsification_route,
        ]
    ).lower()


def _dedupe(values: Iterable[str]) -> tuple[str, ...]:
    deduped: list[str] = []
    for value in values:
        if value and value not in deduped:
            deduped.append(value)
    return tuple(deduped)


def source_verification_status(source: Source) -> tuple[str, str]:
    """Return verification status and residue for a source."""

    if source.url_or_identifier.startswith("source_required:"):
        return "source_placeholder", "Replace placeholder with a primary or credible secondary source."
    if source.source_quality <= 1:
        return "source_required", "Source quality is too low for canon promotion."
    if source.source_quality == 2:
        return "source_found", "Source found but needs corroboration before promotion."
    if source.source_quality >= 4:
        return "source_verified", "Source is strong enough for review, still not automatic canon."
    return "source_found", "Source exists but verification depth is medium."


def build_source_ledger(item: BriefingItem) -> tuple[SourceLedgerEntry, ...]:
    """Create SourceLedger entries for all sources."""

    entries: list[SourceLedgerEntry] = []
    for source in item.sources:
        status, residue = source_verification_status(source)
        entries.append(
            SourceLedgerEntry(
                title=source.title,
                source_type=source.source_type,
                url_or_identifier=source.url_or_identifier,
                source_quality=source.source_quality,
                verification_status=status,
                residue=residue,
            )
        )
    return tuple(entries)


def build_claim_graph(item: BriefingItem) -> tuple[ClaimNode, ...]:
    """Separate factual claims, Tristan inferences, and speculative extensions."""

    claims = [
        ClaimNode("factual_claim", item.why_it_matters, "source_required"),
        ClaimNode("strategic_inference", item.actionable_opportunity, "oak_review_required"),
        ClaimNode("oak_risk", item.oak_check.risk, "active_guardrail"),
        ClaimNode("falsification_route", item.oak_check.falsification_route, "test_required"),
    ]
    if item.business_funding_signal:
        claims.append(ClaimNode("business_inference", item.business_funding_signal, "market_validation_required"))
    if item.ip_signal:
        claims.append(ClaimNode("ip_inference", item.ip_signal, "ip_review_required"))
    return tuple(claims)


def build_evidence_matrix(item: BriefingItem) -> EvidenceMatrix:
    """Build the compact evidence matrix used by SignalGenome++."""

    scores: Mapping[str, int] = item.scores
    source_score = min((source.source_quality for source in item.sources), default=0)
    risk_penalty = _bounded_score(scores.get("hype_penalty", 0)) + _bounded_score(scores.get("source_penalty", 0))
    risk_score = _bounded_score(5 - min(5, risk_penalty))
    prototype_score = _bounded_score(
        max(scores.get("actionability", 0), scores.get("oak_clarity", 0)) if item.oak_check.falsification_route else 0
    )
    residue = item.oak_check.uncertainty or item.oak_check.limit or item.oak_check.risk
    return EvidenceMatrix(
        freshness=_bounded_score(scores.get("freshness", 0)),
        source=_bounded_score(source_score),
        fit=_bounded_score(scores.get("tristan_fit", 0)),
        actionability=_bounded_score(scores.get("actionability", 0)),
        ip=_bounded_score(scores.get("ip_revenue", 0) if item.ip_signal else 0),
        revenue=_bounded_score(scores.get("ip_revenue", 0) if item.business_funding_signal else 0),
        prototype=prototype_score,
        risk=risk_score,
        residue=residue,
    )


def infer_prototype_horizon(item: BriefingItem) -> str:
    """Infer the smallest useful prototype horizon for an item."""

    text = _text_blob(item)
    if "verify" in text or "source" in text:
        return "15_min"
    if "matrix" in text or "tracker" in text or "benchmark" in text:
        return "2_hour"
    if "prototype" in text or "pipeline" in text or "dataset" in text:
        return "1_day"
    if item.final_score >= 28:
        return "1_week"
    return "none"


def build_prototype_ladder(item: BriefingItem) -> PrototypeLadder:
    """Create a reusable P0..P4 prototype ladder."""

    route_name = item.title.replace("`", "")
    return PrototypeLadder(
        p0_15_min=f"Verify source and write one OAK falsification note for: {route_name}.",
        p1_2_hour=f"Create a tiny matrix or benchmark skeleton for: {route_name}.",
        p2_1_day=f"Run one local dry-run and export Markdown/JSON evidence for: {route_name}.",
        p3_1_week=f"Turn the dry-run into a reusable report, issue spec, or dataset for: {route_name}.",
        p4_1_month=f"Evaluate service/software/licensing potential after source and OAK validation for: {route_name}.",
    )


def infer_revenue_routes(item: BriefingItem) -> tuple[str, ...]:
    """Infer plausible, testable revenue routes from item text."""

    text = _text_blob(item)
    routes: list[str] = []
    keyword_routes = {
        "service": "service",
        "audit": "audit",
        "report": "report",
        "template": "template",
        "software": "software",
        "dataset": "dataset",
        "api": "api",
        "grant": "grant",
        "subvention": "grant",
        "consult": "consulting",
        "licensing": "licensing",
        "licence": "licensing",
        "course": "course",
        "veille": "report",
        "prior-art": "service",
        "benchmark": "audit",
    }
    for keyword, route in keyword_routes.items():
        if keyword in text and route not in routes:
            routes.append(route)
    if not routes and item.final_score >= 20:
        routes.append("service")
    return tuple(routes or ["none"])


def build_revenue_physics(item: BriefingItem, routes: tuple[str, ...]) -> RevenuePhysics:
    """Build R0..R8 revenue classification."""

    if routes == ("none",):
        level = "R0_none"
        first = "Do not monetize before source verification and OAK review."
    elif any(route in routes for route in ("licensing", "api")):
        level = "R7_license_or_api"
        first = "Draft a private one-page value hypothesis before public disclosure."
    elif any(route in routes for route in ("software", "dataset", "template")):
        level = "R5_internal_tool"
        first = "Build a reusable internal tool or template and test it on one batch."
    elif any(route in routes for route in ("audit", "report", "consulting", "service")):
        level = "R2_audit_or_report"
        first = "Package one supervised audit/report offer with explicit OAK limits."
    elif "grant" in routes:
        level = "R1_grant_path"
        first = "Create an eligibility checklist and partner map."
    else:
        level = "R1_manual_service"
        first = "Test a manual service with one safe, low-risk deliverable."
    return RevenuePhysics(level=level, routes=routes, first_experiment=first)


def build_agent_security_ledger(item: BriefingItem) -> AgentSecurityLedger:
    """Infer the agent-security posture required by a signal."""

    text = _text_blob(item)
    is_agentic = any(token in text for token in ("agent", "automation", "workflow", "tool", "autonomous"))
    external_action = any(token in text for token in ("payment", "transaction", "email", "external", "write", "deploy", "send"))
    permission_scope = "none"
    if is_agentic and external_action:
        permission_scope = "write_limited"
    elif is_agentic:
        permission_scope = "read_only"
    abuse_cases = ("tool_misuse", "hallucinated_action", "data_exfiltration") if is_agentic else ()
    if external_action:
        abuse_cases = abuse_cases + ("unauthorized_transaction",)
    return AgentSecurityLedger(
        permission_scope=permission_scope,
        human_approval_required=bool(is_agentic),
        rollback_required=bool(is_agentic),
        audit_logs_required=bool(is_agentic),
        abuse_cases=_dedupe(abuse_cases),
    )


def build_observability_signal(item: BriefingItem) -> ObservabilitySignal:
    """Infer the operational metrics required to validate a signal."""

    text = _text_blob(item)
    metrics = ["source_traceability", "oak_residue_count"]
    if any(token in text for token in ("agent", "automation", "workflow")):
        metrics.extend(["task_success_rate", "hallucination_rate", "rollback_events", "human_correction_rate"])
    if any(token in text for token in ("cost", "compute", "gpu", "cloud", "api")):
        metrics.append("cost_per_task")
    if "benchmark" in text or "prototype" in text:
        metrics.append("baseline_delta")
    first_metric = "source_traceability" if item.sources else "source_presence"
    return ObservabilitySignal(metrics=_dedupe(metrics), required=True, first_metric_to_measure=first_metric)


def build_funding_signal(item: BriefingItem) -> FundingSignal:
    """Infer funding and business routes."""

    text = _text_blob(item)
    routes: list[str] = []
    if any(token in text for token in ("grant", "subvention", "fund", "government", "canada", "quebec")):
        routes.extend(["grant_possible", "government_program"])
    if any(token in text for token in ("customer", "enterprise", "audit", "service", "compliance")):
        routes.append("customer_budget_possible")
    if any(token in text for token in ("startup", "venture", "series", "seed", "valuation")):
        routes.append("venture_signal")
    if any(token in text for token in ("research", "lab", "university", "paper")):
        routes.append("research_contract")
    if any(token in text for token in ("partner", "strategic", "supply", "critical")):
        routes.append("strategic_partner")
    routes_tuple = _dedupe(routes) or ("none",)
    strength = "none" if routes_tuple == ("none",) else "medium"
    if len(routes_tuple) >= 3:
        strength = "high"
    first_action = "Create a one-page eligibility/customer hypothesis before outreach." if routes_tuple != ("none",) else "Keep as research signal until a funding route appears."
    return FundingSignal(routes=routes_tuple, strength=strength, first_action=first_action)


def infer_ip_risk_level(item: BriefingItem, ip_classification: str) -> str:
    """Classify public-disclosure/IP risk."""

    text = _text_blob(item)
    if any(token in text for token in ("do not disclose", "secret", "confidential invention")):
        return "danger_do_not_disclose"
    if ip_classification == "confidential_ip_review" or any(token in text for token in ("patentable", "invention", "trade secret")):
        return "high_confidential_invention"
    if ip_classification in {"prior_art_review", "publication_candidate"} or any(token in text for token in ("patent", "prior-art", "paper")):
        return "medium_prior_art_needed"
    return "low_public_signal"


def build_infrastructure_dependency(item: BriefingItem) -> InfrastructureDependency:
    """Infer hidden infrastructure dependencies."""

    text = _text_blob(item)
    keyword_map = {
        "cloud": "cloud",
        "gpu": "gpu",
        "hbm": "hbm",
        "memory": "hbm",
        "energy": "energy",
        "electricity": "energy",
        "data center": "data_center",
        "datacenter": "data_center",
        "submarine": "submarine_cables",
        "cable": "submarine_cables",
        "jurisdiction": "jurisdiction",
        "sanction": "sanctions",
        "export": "export_controls",
        "critical mineral": "critical_minerals",
        "supply chain": "critical_minerals",
    }
    dependencies = _dedupe(dep for keyword, dep in keyword_map.items() if keyword in text)
    if len(dependencies) >= 4:
        risk_level = "high"
    elif dependencies:
        risk_level = "medium"
    else:
        risk_level = "low"
    first_check = "Map compute, energy, jurisdiction, and supply-chain dependencies before promotion."
    if risk_level == "low":
        first_check = "No major infrastructure dependency detected; re-check during OAK review."
    return InfrastructureDependency(dependencies=dependencies or ("none",), risk_level=risk_level, first_check=first_check)


def build_critical_material_dependency(item: BriefingItem) -> CriticalMaterialDependency:
    """Infer critical materials tied to an opportunity."""

    text = _text_blob(item)
    materials = _dedupe(
        material
        for material in (
            "lithium",
            "graphite",
            "nickel",
            "copper",
            "gallium",
            "germanium",
            "indium",
            "rare_earths",
            "niobium",
            "silicon",
            "scandium",
        )
        if material.replace("_", " ") in text or material in text
    )
    if len(materials) >= 3:
        risk_level = "high"
    elif materials:
        risk_level = "medium"
    else:
        risk_level = "low"
    first_check = "Check material availability, supply concentration, substitutes, and ESG constraints."
    if risk_level == "low":
        first_check = "No explicit critical material dependency detected."
    return CriticalMaterialDependency(materials=materials or ("none",), risk_level=risk_level, first_check=first_check)


def build_oak_validation_route(item: BriefingItem, ip_risk_level: str) -> OakValidationRoute:
    """Build the validation route needed before promotion."""

    text = _text_blob(item)
    checks = ["source_check", "oak_risk_check"]
    if any(source.source_quality <= 2 or source.url_or_identifier.startswith("source_required:") for source in item.sources):
        checks.append("source_upgrade_check")
    if any(token in text for token in ("paper", "benchmark", "experiment", "research", "science")):
        checks.extend(["reproduction_check", "baseline_check", "unit_check"])
    if any(token in text for token in ("agent", "automation", "permission", "security")):
        checks.extend(["safety_check", "permission_check", "observability_check"])
    if ip_risk_level in {"medium_prior_art_needed", "high_confidential_invention", "danger_do_not_disclose"}:
        checks.append("ip_check")
    if any(token in text for token in ("customer", "revenue", "service", "audit", "grant")):
        checks.append("customer_or_funding_check")
    if item.final_score >= 20:
        checks.append("prototype_check")
    checks_tuple = _dedupe(checks)
    blocking = "none"
    if "source_upgrade_check" in checks_tuple:
        blocking = "source_upgrade_check"
    elif ip_risk_level in {"high_confidential_invention", "danger_do_not_disclose"}:
        blocking = "ip_check"
    elif "safety_check" in checks_tuple:
        blocking = "safety_check"
    promotion_allowed = blocking == "none"
    return OakValidationRoute(checks=checks_tuple, blocking_check=blocking, promotion_allowed=promotion_allowed)


def infer_canon_status(item: BriefingItem) -> str:
    """Infer conservative canon status from sources and OAK state."""

    if not item.sources:
        return "raw_signal"
    if any(source.source_quality <= 1 or source.url_or_identifier.startswith("source_required:") for source in item.sources):
        return "source_required"
    if item.oak_check.claim_status in {"validated", "measured_result", "validated_result"}:
        return "validated"
    if "patent" in item.signal_type or "prior-art" in _text_blob(item):
        return "prior_art_candidate"
    if item.final_score >= 26 and item.oak_check.falsification_route:
        return "prototype_candidate"
    if item.final_score >= 18:
        return "issue_candidate"
    return "imported_signal"


def compile_signal_genome(item: BriefingItem, *, dry_run: bool = True) -> SignalGenome:
    """Compile one item into a reusable SignalGenome++."""

    route = route_item(item)
    decision = supervise_issue_spec(item, dry_run=dry_run)
    routes = infer_revenue_routes(item)
    ip_risk_level = infer_ip_risk_level(item, route.ip_classification)
    return SignalGenome(
        title=item.title,
        final_score=item.final_score,
        canon_branches=route.branches,
        ip_classification=route.ip_classification,
        issue_type=route.issue_type,
        supervision_mode=decision.mode,
        prototype_horizon=infer_prototype_horizon(item),
        revenue_routes=routes,
        canon_status=infer_canon_status(item),
        m_plus=route.m_plus,
        m_minus=route.m_minus,
        next_action=item.next_action,
        source_ledger=build_source_ledger(item),
        claim_graph=build_claim_graph(item),
        evidence_matrix=build_evidence_matrix(item),
        prototype_ladder=build_prototype_ladder(item),
        revenue_physics=build_revenue_physics(item, routes),
        agent_security_ledger=build_agent_security_ledger(item),
        observability_signal=build_observability_signal(item),
        funding_signal=build_funding_signal(item),
        ip_risk_level=ip_risk_level,
        infrastructure_dependency=build_infrastructure_dependency(item),
        critical_material_dependency=build_critical_material_dependency(item),
        oak_validation_route=build_oak_validation_route(item, ip_risk_level),
    )


def compile_many(items: Iterable[BriefingItem], *, dry_run: bool = True) -> list[SignalGenome]:
    """Compile many Daily Omega items into SignalGenomes."""

    return [compile_signal_genome(item, dry_run=dry_run) for item in items]


def build_daily_dashboard(genomes: Iterable[SignalGenome]) -> dict[str, Any]:
    """Return the dashboard layer for compiled genomes."""

    ranked = sorted(list(genomes), key=lambda genome: genome.final_score, reverse=True)
    if not ranked:
        return {
            "top_signal": None,
            "top_prototype": None,
            "top_revenue": None,
            "top_ip_risk": None,
            "top_oak_warning": None,
            "top_source_to_verify": None,
            "top_next_action": None,
            "top_infrastructure_risk": None,
            "top_agent_security_risk": None,
        }
    top = ranked[0]
    source_to_verify = next(
        (
            genome.title
            for genome in ranked
            for entry in genome.source_ledger
            if entry.verification_status in {"source_placeholder", "source_required", "source_found"}
        ),
        None,
    )
    top_revenue = next((genome.title for genome in ranked if genome.revenue_routes != ("none",)), top.title)
    top_ip = next(
        (genome.title for genome in ranked if genome.ip_risk_level != "low_public_signal"),
        top.title,
    )
    infra = next(
        (genome.title for genome in ranked if genome.infrastructure_dependency.risk_level in {"medium", "high"}),
        None,
    )
    agent_security = next(
        (genome.title for genome in ranked if genome.agent_security_ledger.permission_scope != "none"),
        None,
    )
    return {
        "top_signal": top.title,
        "top_prototype": top.prototype_ladder.p0_15_min,
        "top_revenue": top_revenue,
        "top_ip_risk": top_ip,
        "top_oak_warning": top.m_minus,
        "top_source_to_verify": source_to_verify,
        "top_next_action": top.next_action,
        "top_infrastructure_risk": infra,
        "top_agent_security_risk": agent_security,
    }


def render_intelligence_os_markdown(genomes: Iterable[SignalGenome]) -> str:
    """Render a compact Intelligence OS report section."""

    genome_list = list(genomes)
    dashboard = build_daily_dashboard(genome_list)
    lines = ["# Daily Ω Intelligence OS", "", "## Dashboard", ""]
    for key, value in dashboard.items():
        lines.append(f"- **{key}:** {value if value is not None else 'None'}")
    lines.append("")
    for index, genome in enumerate(genome_list, start=1):
        lines.extend(
            [
                f"## {index}. {genome.title}",
                f"- **Score:** {genome.final_score}",
                f"- **Canon status:** {genome.canon_status}",
                f"- **Branches:** {', '.join(genome.canon_branches) or 'Unrouted'}",
                f"- **IP:** {genome.ip_classification}",
                f"- **IP risk:** {genome.ip_risk_level}",
                f"- **Issue type:** {genome.issue_type}",
                f"- **Supervisor:** {genome.supervision_mode}",
                f"- **Prototype horizon:** {genome.prototype_horizon}",
                f"- **Revenue routes:** {', '.join(genome.revenue_routes)}",
                f"- **Funding signal:** {genome.funding_signal.strength} / {', '.join(genome.funding_signal.routes)}",
                f"- **Revenue physics:** {genome.revenue_physics.level}",
                f"- **Agent security:** {genome.agent_security_ledger.permission_scope}",
                f"- **Infrastructure:** {genome.infrastructure_dependency.risk_level} / {', '.join(genome.infrastructure_dependency.dependencies)}",
                f"- **Critical materials:** {genome.critical_material_dependency.risk_level} / {', '.join(genome.critical_material_dependency.materials)}",
                f"- **OAK validation:** blocking={genome.oak_validation_route.blocking_check}; checks={', '.join(genome.oak_validation_route.checks)}",
                f"- **Source status:** {', '.join(entry.verification_status for entry in genome.source_ledger)}",
                f"- **Evidence residue:** {genome.evidence_matrix.residue}",
                f"- **M-:** {genome.m_minus}",
                f"- **Next action:** {genome.next_action}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


__all__ = [
    "CANON_STATUS_LADDER",
    "PROTOTYPE_HORIZONS",
    "REVENUE_ROUTES",
    "AgentSecurityLedger",
    "ClaimNode",
    "CriticalMaterialDependency",
    "EvidenceMatrix",
    "FundingSignal",
    "InfrastructureDependency",
    "OakValidationRoute",
    "ObservabilitySignal",
    "PrototypeLadder",
    "RevenuePhysics",
    "SignalGenome",
    "SourceLedgerEntry",
    "build_agent_security_ledger",
    "build_claim_graph",
    "build_critical_material_dependency",
    "build_daily_dashboard",
    "build_evidence_matrix",
    "build_funding_signal",
    "build_infrastructure_dependency",
    "build_oak_validation_route",
    "build_observability_signal",
    "build_prototype_ladder",
    "build_revenue_physics",
    "build_source_ledger",
    "compile_many",
    "compile_signal_genome",
    "infer_canon_status",
    "infer_ip_risk_level",
    "infer_prototype_horizon",
    "infer_revenue_routes",
    "render_intelligence_os_markdown",
    "source_verification_status",
]
