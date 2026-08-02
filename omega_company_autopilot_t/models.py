"""Typed records for Ω-COMPANY-AUTOPILOT-T.

The package models corporate operations without pretending to perform legal,
tax, banking, securities, or government acts. Operator-supplied evidence is
always explicit and nullable.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Iterable


class CompanyState(str, Enum):
    IDEA = "IDEA"
    CANDIDATE_LEGAL_ENTITY = "CANDIDATE_LEGAL_ENTITY"
    PROFESSIONAL_REVIEW = "PROFESSIONAL_REVIEW"
    FILING_READY = "FILING_READY"
    FILING_SUBMITTED = "FILING_SUBMITTED"
    REGISTERED = "REGISTERED"
    INCORPORATED = "INCORPORATED"
    POST_FORMATION = "POST_FORMATION"
    OPERATING = "OPERATING"
    PRODUCTION_AUTHORIZED = "PRODUCTION_AUTHORIZED"
    M_MINUS_HOLD = "M_MINUS_HOLD"


class AutonomyLevel(int, Enum):
    L0_MANUAL = 0
    L1_ASSIST = 1
    L2_PREPARE = 2
    L3_APPROVAL = 3
    L4_BOUNDED = 4
    L5_SUPERVISED = 5


class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ActionKind(str, Enum):
    INTERNAL_REPORT = "INTERNAL_REPORT"
    INTERNAL_MESSAGE = "INTERNAL_MESSAGE"
    EXTERNAL_EMAIL = "EXTERNAL_EMAIL"
    CUSTOMER_SUPPORT = "CUSTOMER_SUPPORT"
    INVOICE_DRAFT = "INVOICE_DRAFT"
    INVOICE_SEND = "INVOICE_SEND"
    PAYMENT_PREPARE = "PAYMENT_PREPARE"
    PAYMENT_EXECUTE = "PAYMENT_EXECUTE"
    CONTRACT_DRAFT = "CONTRACT_DRAFT"
    CONTRACT_ACCEPT = "CONTRACT_ACCEPT"
    GOVERNMENT_FILING_PREPARE = "GOVERNMENT_FILING_PREPARE"
    GOVERNMENT_FILING_SUBMIT = "GOVERNMENT_FILING_SUBMIT"
    TAX_RETURN_PREPARE = "TAX_RETURN_PREPARE"
    TAX_RETURN_FILE = "TAX_RETURN_FILE"
    BANK_ACCOUNT_OPEN = "BANK_ACCOUNT_OPEN"
    SHARE_ISSUANCE = "SHARE_ISSUANCE"
    IP_CLASSIFY = "IP_CLASSIFY"
    IP_PUBLISH = "IP_PUBLISH"
    IP_ASSIGN = "IP_ASSIGN"
    HIRE_PREPARE = "HIRE_PREPARE"
    HIRE_COMMIT = "HIRE_COMMIT"
    DOMAIN_RENEW = "DOMAIN_RENEW"
    DNS_CHANGE = "DNS_CHANGE"
    DATA_DELETE = "DATA_DELETE"
    SECURITY_CONTAIN = "SECURITY_CONTAIN"
    PUBLIC_CLAIM = "PUBLIC_CLAIM"


class GateDecision(str, Enum):
    AUTO = "AUTO"
    PREPARE = "PREPARE"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    REQUIRE_TWO_APPROVALS = "REQUIRE_TWO_APPROVALS"
    PROFESSIONAL_REVIEW = "PROFESSIONAL_REVIEW"
    BLOCK = "BLOCK"


class ActionStatus(str, Enum):
    PROPOSED = "PROPOSED"
    GATED = "GATED"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DRY_RUN_COMPLETE = "DRY_RUN_COMPLETE"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    evidence_id: str
    kind: str
    location: str
    sha256: str | None = None
    verified: bool = False
    verified_by: str | None = None
    verified_at: str | None = None
    redacted: bool = True


@dataclass(slots=True)
class DivisionRecord:
    division_id: str
    display_name: str
    mission: str
    status: str = "internal_division"
    owner_company_id: str | None = None
    autonomy_level: AutonomyLevel = AutonomyLevel.L2_PREPARE
    annual_budget_cad: float = 0.0
    revenue_cad: float = 0.0
    recurring_revenue_cad: float = 0.0
    active_customers: int = 0
    paid_pilots: int = 0
    external_partners: int = 0
    ip_assets: int = 0
    regulated_activity: bool = False
    liability_isolation_need: float = 0.0
    investor_interest: float = 0.0
    administrative_cost_cad: float = 0.0
    enabled: bool = True


@dataclass(slots=True)
class CompanyRecord:
    company_id: str
    conceptual_name: str
    jurisdiction: str = "QC"
    state: CompanyState = CompanyState.CANDIDATE_LEGAL_ENTITY
    legal_name: str | None = None
    operating_names: list[str] = field(default_factory=list)
    legal_form: str | None = None
    incorporation_number: str | None = None
    neq: str | None = None
    cra_business_number: str | None = None
    legal_identity_verified: bool = False
    registry_snapshot_verified: bool = False
    privacy_officer: str | None = None
    directors: list[str] = field(default_factory=list)
    shareholders: list[str] = field(default_factory=list)
    officers: list[str] = field(default_factory=list)
    divisions: list[DivisionRecord] = field(default_factory=list)
    autonomy_level: AutonomyLevel = AutonomyLevel.L2_PREPARE
    external_mail_enabled: bool = False
    banking_enabled: bool = False
    invoice_send_enabled: bool = False
    contract_acceptance_enabled: bool = False
    production_enabled: bool = False
    evidence: list[EvidenceRef] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def division(self, division_id: str) -> DivisionRecord:
        for division in self.divisions:
            if division.division_id == division_id:
                return division
        raise KeyError(division_id)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["state"] = self.state.value
        payload["autonomy_level"] = int(self.autonomy_level)
        for division in payload["divisions"]:
            division["autonomy_level"] = int(division["autonomy_level"])
        return payload


@dataclass(frozen=True, slots=True)
class Obligation:
    obligation_id: str
    company_id: str
    title: str
    due_date: date
    category: str
    jurisdiction: str
    source: str
    evidence_required: tuple[str, ...] = ()
    approval_required: bool = True
    professional_review_required: bool = False
    recurrence: str | None = None
    completed: bool = False


@dataclass(frozen=True, slots=True)
class DeadlineEvent:
    obligation_id: str
    event_date: date
    offset_days: int
    severity: str
    action: str


@dataclass(slots=True)
class ActionRequest:
    action_id: str
    company_id: str
    division_id: str | None
    kind: ActionKind
    title: str
    payload: dict[str, Any]
    risk_level: RiskLevel = RiskLevel.MODERATE
    reversible: bool = True
    external_effect: bool = False
    amount_cad: float | None = None
    counterparty: str | None = None
    requested_by: str = "company_autopilot"
    status: ActionStatus = ActionStatus.PROPOSED
    content_hash: str | None = None
    evidence_ids: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class ApprovalRecord:
    approval_id: str
    action_id: str
    approver: str
    decision: str
    action_hash: str
    reason: str
    approved_at: str
    expires_at: str | None = None


@dataclass(frozen=True, slots=True)
class GateResult:
    action_id: str
    decision: GateDecision
    reasons: tuple[str, ...]
    required_approvals: int = 0
    professional_review: tuple[str, ...] = ()
    required_evidence: tuple[str, ...] = ()
    max_amount_cad: float | None = None

    @property
    def executable(self) -> bool:
        return self.decision in {GateDecision.AUTO, GateDecision.REQUIRE_APPROVAL, GateDecision.REQUIRE_TWO_APPROVALS}


@dataclass(frozen=True, slots=True)
class TreasuryPolicy:
    currency: str = "CAD"
    auto_execute_enabled: bool = False
    known_vendor_limit_cad: float = 100.0
    single_approval_limit_cad: float = 1_000.0
    two_approval_threshold_cad: float = 1_000.0
    prohibited_categories: tuple[str, ...] = (
        "tax_payment",
        "government_fee",
        "salary",
        "dividend",
        "shareholder_loan",
        "international_wire",
        "crypto_transfer",
        "new_vendor",
    )
    reserve_tax_fraction: float = 0.20
    reserve_operating_fraction: float = 0.20
    reserve_rnd_fraction: float = 0.15


@dataclass(frozen=True, slots=True)
class TreasuryAllocation:
    gross_cad: float
    tax_reserve_cad: float
    operating_reserve_cad: float
    rnd_reserve_cad: float
    available_cad: float


@dataclass(frozen=True, slots=True)
class ExecutionReceipt:
    action_id: str
    provider: str
    mode: str
    accepted: bool
    executed_at: str
    external_reference: str | None
    action_hash: str
    notes: tuple[str, ...] = ()


def enum_value(value: Any, enum_type: type[Enum]) -> Enum:
    if isinstance(value, enum_type):
        return value
    return enum_type(value)


def evidence_ids(items: Iterable[EvidenceRef]) -> set[str]:
    return {item.evidence_id for item in items if item.verified}
