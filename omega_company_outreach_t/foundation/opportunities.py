from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum
import math
from typing import Iterable, Mapping, Sequence

from .canonical import (
    CanonicalizationError,
    assert_public_safe_text,
    canonical_hash,
    ensure_utc,
    is_sha256,
    normalize_text,
    stable_unique,
    utc_now,
    validate_public_identifier,
)


class OpportunityType(str, Enum):
    ENTREPRENEURSHIP_PROGRAM = "entrepreneurship_program"
    FINANCING_PROGRAM = "financing_program"
    STRATEGIC_PARTNERSHIP = "strategic_partnership"
    RESEARCH_PILOT = "research_pilot"
    SOFTWARE_PILOT = "software_pilot"
    AUDIT_SERVICE = "audit_service"
    SECURITY_REVIEW = "security_review"
    DATA_PARTNERSHIP = "data_partnership"
    PUBLICATION = "publication"
    GRANT = "grant"
    PROCUREMENT = "procurement"
    OPEN_SOURCE_COLLABORATION = "open_source_collaboration"
    INTEGRATION = "integration"
    LICENSING = "licensing"
    ADVISORY = "advisory"
    REFERRAL = "referral"


class OpportunityState(str, Enum):
    DISCOVERED = "discovered"
    NEEDS_EVIDENCE = "needs_evidence"
    QUALIFIED = "qualified"
    ACTIVE = "active"
    WAITING = "waiting"
    MEETING = "meeting"
    PILOT = "pilot"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"
    ARCHIVED = "archived"
    BLOCKED = "blocked"


class PortfolioAction(str, Enum):
    ACT_NOW = "act_now"
    PREPARE_EVIDENCE = "prepare_evidence"
    REQUEST_REFERRAL = "request_referral"
    WAIT_FOR_EVENT = "wait_for_event"
    BUILD_ASSET_FIRST = "build_asset_first"
    ARCHIVE_FERTILE = "archive_fertile"
    BLOCK = "block"


class CompanyUnit(str, Enum):
    PARENT = "tristan_parent_opco"
    OAK = "tristan_oak_systems"
    SOFTWARE = "tristan_software_labs"
    RESEARCH = "tristan_research_foundry"


@dataclass(frozen=True, slots=True)
class StrategicSignals:
    relevance: float
    authority: float
    problem_fit: float
    asset_readiness: float
    evidence: float
    timing: float
    reciprocity: float
    expected_value: float
    probability_response: float
    probability_conversion: float
    optionality: float
    effort_cost: float
    legal_risk: float
    reputation_risk: float
    privacy_risk: float
    maintenance_cost: float
    opportunity_cost: float

    def __post_init__(self) -> None:
        for name, value in self.as_mapping().items():
            if not 0.0 <= value <= 1.0:
                raise CanonicalizationError(f"strategic signal {name} must be between 0 and 1")

    def as_mapping(self) -> dict[str, float]:
        return {
            "relevance": self.relevance,
            "authority": self.authority,
            "problem_fit": self.problem_fit,
            "asset_readiness": self.asset_readiness,
            "evidence": self.evidence,
            "timing": self.timing,
            "reciprocity": self.reciprocity,
            "expected_value": self.expected_value,
            "probability_response": self.probability_response,
            "probability_conversion": self.probability_conversion,
            "optionality": self.optionality,
            "effort_cost": self.effort_cost,
            "legal_risk": self.legal_risk,
            "reputation_risk": self.reputation_risk,
            "privacy_risk": self.privacy_risk,
            "maintenance_cost": self.maintenance_cost,
            "opportunity_cost": self.opportunity_cost,
        }

    @property
    def positive_geometric_mean(self) -> float:
        positive = (
            self.relevance,
            self.authority,
            self.problem_fit,
            self.asset_readiness,
            self.evidence,
            self.timing,
            self.reciprocity,
            self.expected_value,
            self.probability_response,
            self.probability_conversion,
            self.optionality,
        )
        epsilon = 1e-6
        return math.exp(sum(math.log(max(epsilon, value)) for value in positive) / len(positive))

    @property
    def risk_burden(self) -> float:
        risks = (
            self.effort_cost,
            self.legal_risk,
            self.reputation_risk,
            self.privacy_risk,
            self.maintenance_cost,
            self.opportunity_cost,
        )
        return sum(risks) / len(risks)

    @property
    def score_100(self) -> int:
        positive = self.positive_geometric_mean
        risk_multiplier = max(0.0, 1.0 - 0.72 * self.risk_burden)
        return max(0, min(100, round(100 * positive * risk_multiplier)))

    @property
    def signal_hash(self) -> str:
        return canonical_hash(self)


@dataclass(frozen=True, slots=True)
class BayesianStage:
    stage: str
    alpha: float
    beta: float
    observations: int = 0

    def __post_init__(self) -> None:
        stage = normalize_text(self.stage).casefold().replace(" ", "_")
        if not stage:
            raise CanonicalizationError("Bayesian stage is required")
        if self.alpha <= 0 or self.beta <= 0:
            raise CanonicalizationError("Bayesian alpha and beta must be positive")
        if self.observations < 0:
            raise CanonicalizationError("Bayesian observations cannot be negative")
        object.__setattr__(self, "stage", stage)

    @property
    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    @property
    def uncertainty(self) -> float:
        total = self.alpha + self.beta
        variance = (self.alpha * self.beta) / (total * total * (total + 1.0))
        return math.sqrt(variance)

    def update(self, *, success: bool, weight: float = 1.0) -> "BayesianStage":
        if weight <= 0:
            raise CanonicalizationError("Bayesian observation weight must be positive")
        return BayesianStage(
            stage=self.stage,
            alpha=self.alpha + (weight if success else 0.0),
            beta=self.beta + (0.0 if success else weight),
            observations=self.observations + 1,
        )


@dataclass(frozen=True, slots=True)
class OpportunityPosterior:
    response: BayesianStage = field(
        default_factory=lambda: BayesianStage("response", 2.0, 3.0)
    )
    meeting_given_response: BayesianStage = field(
        default_factory=lambda: BayesianStage("meeting_given_response", 2.0, 2.0)
    )
    pilot_given_meeting: BayesianStage = field(
        default_factory=lambda: BayesianStage("pilot_given_meeting", 1.5, 2.5)
    )
    payment_given_pilot: BayesianStage = field(
        default_factory=lambda: BayesianStage("payment_given_pilot", 1.2, 3.0)
    )

    @property
    def expected_payment_probability(self) -> float:
        return (
            self.response.mean
            * self.meeting_given_response.mean
            * self.pilot_given_meeting.mean
            * self.payment_given_pilot.mean
        )

    @property
    def posterior_hash(self) -> str:
        return canonical_hash(self)

    def observe(self, event: str, *, success: bool, weight: float = 1.0) -> "OpportunityPosterior":
        normalized = normalize_text(event).casefold().replace(" ", "_")
        if normalized == "response":
            return replace(self, response=self.response.update(success=success, weight=weight))
        if normalized == "meeting_given_response":
            return replace(
                self,
                meeting_given_response=self.meeting_given_response.update(
                    success=success, weight=weight
                ),
            )
        if normalized == "pilot_given_meeting":
            return replace(
                self,
                pilot_given_meeting=self.pilot_given_meeting.update(
                    success=success, weight=weight
                ),
            )
        if normalized == "payment_given_pilot":
            return replace(
                self,
                payment_given_pilot=self.payment_given_pilot.update(
                    success=success, weight=weight
                ),
            )
        raise CanonicalizationError(f"unknown posterior event: {event}")


@dataclass(frozen=True, slots=True)
class Opportunity:
    opportunity_id: str
    organization_id: str
    company_unit: CompanyUnit
    opportunity_type: OpportunityType
    state: OpportunityState
    problem_statement: str
    proposed_asset_id: str
    evidence_hashes: tuple[str, ...]
    signals: StrategicSignals
    posterior: OpportunityPosterior = field(default_factory=OpportunityPosterior)
    contact_id: str | None = None
    source_issue: int | None = None
    estimated_effort_hours: float = 1.0
    expected_value_cad: int | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    tags: tuple[str, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "opportunity_id",
            validate_public_identifier(self.opportunity_id, prefix="OPP"),
        )
        object.__setattr__(
            self,
            "organization_id",
            validate_public_identifier(self.organization_id, prefix="ORG"),
        )
        if self.contact_id:
            object.__setattr__(
                self,
                "contact_id",
                validate_public_identifier(self.contact_id, prefix="CNT"),
            )
        problem = normalize_text(self.problem_statement)
        assert_public_safe_text(problem, field="opportunity problem", maximum=3000)
        if not problem:
            raise CanonicalizationError("opportunity problem_statement is required")
        asset = normalize_text(self.proposed_asset_id).casefold().replace(" ", "_")
        if not asset:
            raise CanonicalizationError("proposed_asset_id is required")
        if not self.evidence_hashes:
            raise CanonicalizationError("opportunity requires evidence hashes")
        if any(not is_sha256(value) for value in self.evidence_hashes):
            raise CanonicalizationError("all opportunity evidence hashes must be SHA-256")
        if self.estimated_effort_hours <= 0 or self.estimated_effort_hours > 10000:
            raise CanonicalizationError("estimated_effort_hours is outside valid range")
        if self.expected_value_cad is not None and self.expected_value_cad < 0:
            raise CanonicalizationError("expected_value_cad cannot be negative")
        created_at = ensure_utc(self.created_at)
        updated_at = ensure_utc(self.updated_at)
        if updated_at < created_at:
            raise CanonicalizationError("opportunity updated_at cannot precede created_at")
        if self.state not in {OpportunityState.DISCOVERED, OpportunityState.NEEDS_EVIDENCE}:
            if self.signals.evidence < 0.20:
                raise CanonicalizationError("qualified opportunity has insufficient evidence signal")
        object.__setattr__(self, "problem_statement", problem)
        object.__setattr__(self, "proposed_asset_id", asset)
        object.__setattr__(self, "evidence_hashes", tuple(sorted(set(self.evidence_hashes))))
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "updated_at", updated_at)
        object.__setattr__(self, "tags", stable_unique(self.tags))
        object.__setattr__(self, "metadata", dict(sorted(self.metadata.items())))

    @property
    def opportunity_hash(self) -> str:
        return canonical_hash(self)

    @property
    def deduplication_key(self) -> str:
        normalized_problem = " ".join(
            token for token in self.problem_statement.casefold().split() if len(token) > 2
        )
        return canonical_hash(
            {
                "organization_id": self.organization_id,
                "opportunity_type": self.opportunity_type.value,
                "asset": self.proposed_asset_id,
                "problem": normalized_problem,
            }
        )

    @property
    def strategic_score(self) -> int:
        posterior_factor = 0.75 + min(0.25, self.posterior.response.mean * 0.25)
        return max(0, min(100, round(self.signals.score_100 * posterior_factor)))

    @property
    def expected_pipeline_value_cad(self) -> float | None:
        if self.expected_value_cad is None:
            return None
        return self.expected_value_cad * self.posterior.expected_payment_probability

    def transition(self, target: OpportunityState, *, now: datetime | None = None) -> "Opportunity":
        allowed = {
            OpportunityState.DISCOVERED: frozenset(
                {
                    OpportunityState.NEEDS_EVIDENCE,
                    OpportunityState.QUALIFIED,
                    OpportunityState.ARCHIVED,
                    OpportunityState.BLOCKED,
                }
            ),
            OpportunityState.NEEDS_EVIDENCE: frozenset(
                {
                    OpportunityState.QUALIFIED,
                    OpportunityState.ARCHIVED,
                    OpportunityState.BLOCKED,
                }
            ),
            OpportunityState.QUALIFIED: frozenset(
                {
                    OpportunityState.ACTIVE,
                    OpportunityState.WAITING,
                    OpportunityState.ARCHIVED,
                    OpportunityState.BLOCKED,
                }
            ),
            OpportunityState.ACTIVE: frozenset(
                {
                    OpportunityState.WAITING,
                    OpportunityState.MEETING,
                    OpportunityState.PILOT,
                    OpportunityState.PROPOSAL,
                    OpportunityState.LOST,
                    OpportunityState.BLOCKED,
                }
            ),
            OpportunityState.WAITING: frozenset(
                {
                    OpportunityState.ACTIVE,
                    OpportunityState.MEETING,
                    OpportunityState.LOST,
                    OpportunityState.ARCHIVED,
                    OpportunityState.BLOCKED,
                }
            ),
            OpportunityState.MEETING: frozenset(
                {
                    OpportunityState.ACTIVE,
                    OpportunityState.PILOT,
                    OpportunityState.PROPOSAL,
                    OpportunityState.LOST,
                }
            ),
            OpportunityState.PILOT: frozenset(
                {OpportunityState.PROPOSAL, OpportunityState.WON, OpportunityState.LOST}
            ),
            OpportunityState.PROPOSAL: frozenset(
                {
                    OpportunityState.NEGOTIATION,
                    OpportunityState.WON,
                    OpportunityState.LOST,
                }
            ),
            OpportunityState.NEGOTIATION: frozenset(
                {OpportunityState.WON, OpportunityState.LOST, OpportunityState.PROPOSAL}
            ),
            OpportunityState.WON: frozenset(),
            OpportunityState.LOST: frozenset(
                {OpportunityState.QUALIFIED, OpportunityState.ARCHIVED}
            ),
            OpportunityState.ARCHIVED: frozenset({OpportunityState.QUALIFIED}),
            OpportunityState.BLOCKED: frozenset({OpportunityState.ARCHIVED}),
        }
        if target not in allowed[self.state]:
            raise CanonicalizationError(
                f"opportunity transition {self.state.value} -> {target.value} is forbidden"
            )
        return replace(self, state=target, updated_at=now or utc_now())

    def observe_stage(
        self,
        event: str,
        *,
        success: bool,
        weight: float = 1.0,
        now: datetime | None = None,
    ) -> "Opportunity":
        return replace(
            self,
            posterior=self.posterior.observe(event, success=success, weight=weight),
            updated_at=now or utc_now(),
        )


def route_opportunity(opportunity_type: OpportunityType) -> CompanyUnit:
    if opportunity_type in {
        OpportunityType.ENTREPRENEURSHIP_PROGRAM,
        OpportunityType.FINANCING_PROGRAM,
        OpportunityType.STRATEGIC_PARTNERSHIP,
        OpportunityType.GRANT,
        OpportunityType.REFERRAL,
    }:
        return CompanyUnit.PARENT
    if opportunity_type in {
        OpportunityType.AUDIT_SERVICE,
        OpportunityType.SECURITY_REVIEW,
    }:
        return CompanyUnit.OAK
    if opportunity_type in {
        OpportunityType.SOFTWARE_PILOT,
        OpportunityType.INTEGRATION,
        OpportunityType.LICENSING,
        OpportunityType.PROCUREMENT,
    }:
        return CompanyUnit.SOFTWARE
    return CompanyUnit.RESEARCH


def recommend_action(opportunity: Opportunity) -> PortfolioAction:
    if opportunity.state is OpportunityState.BLOCKED:
        return PortfolioAction.BLOCK
    if opportunity.signals.legal_risk >= 0.80 or opportunity.signals.privacy_risk >= 0.80:
        return PortfolioAction.BLOCK
    if opportunity.state is OpportunityState.NEEDS_EVIDENCE or opportunity.signals.evidence < 0.45:
        return PortfolioAction.PREPARE_EVIDENCE
    if opportunity.signals.asset_readiness < 0.40:
        return PortfolioAction.BUILD_ASSET_FIRST
    if opportunity.state is OpportunityState.WAITING:
        return PortfolioAction.WAIT_FOR_EVENT
    if opportunity.opportunity_type is OpportunityType.REFERRAL:
        return PortfolioAction.REQUEST_REFERRAL
    if opportunity.strategic_score >= 68 and opportunity.state in {
        OpportunityState.QUALIFIED,
        OpportunityState.ACTIVE,
        OpportunityState.MEETING,
        OpportunityState.PILOT,
        OpportunityState.PROPOSAL,
    }:
        return PortfolioAction.ACT_NOW
    if opportunity.strategic_score >= 45:
        return PortfolioAction.WAIT_FOR_EVENT
    return PortfolioAction.ARCHIVE_FERTILE


@dataclass(frozen=True, slots=True)
class PortfolioLimits:
    active_priority_cases: int = 8
    maximum_open_cases: int = 12
    high_risk_cases_in_parallel: int = 1
    effort_budget_hours: float = 40.0
    minimum_score: int = 45

    def __post_init__(self) -> None:
        if self.active_priority_cases < 1:
            raise CanonicalizationError("active_priority_cases must be positive")
        if self.maximum_open_cases < self.active_priority_cases:
            raise CanonicalizationError("maximum_open_cases cannot be below active_priority_cases")
        if self.high_risk_cases_in_parallel < 0:
            raise CanonicalizationError("high_risk_cases_in_parallel cannot be negative")
        if self.effort_budget_hours <= 0:
            raise CanonicalizationError("effort budget must be positive")
        if not 0 <= self.minimum_score <= 100:
            raise CanonicalizationError("minimum score must be between 0 and 100")


@dataclass(frozen=True, slots=True)
class PortfolioSelection:
    selected_ids: tuple[str, ...]
    deferred_ids: tuple[str, ...]
    blocked_ids: tuple[str, ...]
    total_effort_hours: float
    expected_pipeline_value_cad: float
    reasons: Mapping[str, tuple[str, ...]]

    @property
    def selection_hash(self) -> str:
        return canonical_hash(self)


def allocate_portfolio(
    opportunities: Sequence[Opportunity], limits: PortfolioLimits = PortfolioLimits()
) -> PortfolioSelection:
    active_states = {
        OpportunityState.QUALIFIED,
        OpportunityState.ACTIVE,
        OpportunityState.WAITING,
        OpportunityState.MEETING,
        OpportunityState.PILOT,
        OpportunityState.PROPOSAL,
        OpportunityState.NEGOTIATION,
    }
    candidates = [item for item in opportunities if item.state in active_states]
    if len(candidates) > limits.maximum_open_cases:
        candidates = sorted(candidates, key=lambda item: (-item.strategic_score, item.opportunity_id))[
            : limits.maximum_open_cases
        ]
    def utility(item: Opportunity) -> float:
        pipeline = item.expected_pipeline_value_cad or 0.0
        value_component = math.log1p(pipeline) / 12.0
        effort_penalty = min(1.0, item.estimated_effort_hours / 80.0)
        return item.strategic_score / 100.0 + value_component - 0.30 * effort_penalty

    ordered = sorted(candidates, key=lambda item: (-utility(item), item.opportunity_id))
    selected: list[str] = []
    deferred: list[str] = []
    blocked: list[str] = []
    reasons: dict[str, tuple[str, ...]] = {}
    effort = 0.0
    high_risk_count = 0
    expected_pipeline_value = 0.0
    for opportunity in ordered:
        action = recommend_action(opportunity)
        risk = max(
            opportunity.signals.legal_risk,
            opportunity.signals.reputation_risk,
            opportunity.signals.privacy_risk,
        )
        if action is PortfolioAction.BLOCK:
            blocked.append(opportunity.opportunity_id)
            reasons[opportunity.opportunity_id] = ("policy block",)
            continue
        if opportunity.strategic_score < limits.minimum_score:
            deferred.append(opportunity.opportunity_id)
            reasons[opportunity.opportunity_id] = ("below portfolio minimum score",)
            continue
        if len(selected) >= limits.active_priority_cases:
            deferred.append(opportunity.opportunity_id)
            reasons[opportunity.opportunity_id] = ("active priority capacity reached",)
            continue
        if effort + opportunity.estimated_effort_hours > limits.effort_budget_hours:
            deferred.append(opportunity.opportunity_id)
            reasons[opportunity.opportunity_id] = ("effort budget exceeded",)
            continue
        if risk >= 0.60 and high_risk_count >= limits.high_risk_cases_in_parallel:
            deferred.append(opportunity.opportunity_id)
            reasons[opportunity.opportunity_id] = ("high-risk concurrency limit reached",)
            continue
        selected.append(opportunity.opportunity_id)
        effort += opportunity.estimated_effort_hours
        if risk >= 0.60:
            high_risk_count += 1
        expected_pipeline_value += opportunity.expected_pipeline_value_cad or 0.0
        reasons[opportunity.opportunity_id] = (
            f"selected with score {opportunity.strategic_score}",
            f"recommended action {action.value}",
        )
    all_ids = {item.opportunity_id for item in opportunities}
    classified = set(selected) | set(deferred) | set(blocked)
    for identifier in sorted(all_ids - classified):
        deferred.append(identifier)
        reasons[identifier] = ("outside active portfolio states",)
    return PortfolioSelection(
        selected_ids=tuple(selected),
        deferred_ids=tuple(sorted(set(deferred))),
        blocked_ids=tuple(sorted(set(blocked))),
        total_effort_hours=round(effort, 3),
        expected_pipeline_value_cad=round(expected_pipeline_value, 2),
        reasons=dict(sorted(reasons.items())),
    )


def audit_opportunities(opportunities: Iterable[Opportunity]) -> list[str]:
    materialized = tuple(opportunities)
    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_keys: dict[str, str] = {}
    for opportunity in materialized:
        if opportunity.opportunity_id in seen_ids:
            errors.append(f"duplicate opportunity_id: {opportunity.opportunity_id}")
        seen_ids.add(opportunity.opportunity_id)
        if opportunity.deduplication_key in seen_keys:
            errors.append(
                f"duplicate opportunity: {opportunity.opportunity_id} and "
                f"{seen_keys[opportunity.deduplication_key]}"
            )
        else:
            seen_keys[opportunity.deduplication_key] = opportunity.opportunity_id
        expected_company = route_opportunity(opportunity.opportunity_type)
        if opportunity.company_unit is not expected_company:
            errors.append(
                f"{opportunity.opportunity_id}: expected company {expected_company.value}, "
                f"got {opportunity.company_unit.value}"
            )
        if opportunity.state is OpportunityState.WON and opportunity.expected_value_cad is None:
            errors.append(f"{opportunity.opportunity_id}: won opportunity lacks expected value")
        if opportunity.strategic_score >= 75 and opportunity.state is OpportunityState.ARCHIVED:
            errors.append(f"{opportunity.opportunity_id}: high-score opportunity is archived")
    return errors
