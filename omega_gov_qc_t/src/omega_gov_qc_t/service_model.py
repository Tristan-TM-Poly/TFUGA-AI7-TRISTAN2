"""Public service primitives for Ω-GOV-QC-T."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal

ServiceChannel = Literal["web", "phone", "office", "mail", "email", "api", "mobile", "other"]
OAKStatus = Literal["A", "B", "C", "D", "M-", "blocked"]


@dataclass(frozen=True)
class PublicService:
    """A reviewable public service unit.

    This model describes service structure, not eligibility decisions. It is
    safe for open-data mapping, documentation, friction analysis and report
    generation.
    """

    service_id: str
    name: str
    responsible_entity: str
    target_users: List[str] = field(default_factory=list)
    required_documents: List[str] = field(default_factory=list)
    forms: List[str] = field(default_factory=list)
    channels: List[ServiceChannel] = field(default_factory=list)
    data_used: List[str] = field(default_factory=list)
    appeal_or_review_path: str = ""
    human_contact_required: bool = True
    oak_status: OAKStatus = "B"
    average_delay_days: float | None = None
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not self.service_id.strip():
            errors.append("service_id is required")
        if not self.name.strip():
            errors.append("name is required")
        if not self.responsible_entity.strip():
            errors.append("responsible_entity is required")
        if self.average_delay_days is not None and self.average_delay_days < 0:
            errors.append("average_delay_days cannot be negative")
        for channel in self.channels:
            if channel not in ServiceChannel.__args__:  # type: ignore[attr-defined]
                errors.append(f"invalid channel: {channel}")
        return errors

    @property
    def document_burden(self) -> int:
        return len(self.required_documents) + len(self.forms)

    @property
    def has_review_path(self) -> bool:
        return bool(self.appeal_or_review_path.strip())

    @property
    def is_ready_for_public_mapping(self) -> bool:
        return not self.validate() and bool(self.channels) and self.human_contact_required

    def friction_signals(self) -> List[str]:
        signals: List[str] = []
        if self.document_burden >= 6:
            signals.append("high_document_burden")
        if not self.channels:
            signals.append("missing_service_channel")
        if not self.has_review_path:
            signals.append("missing_review_path")
        if self.average_delay_days is not None and self.average_delay_days > 30:
            signals.append("long_average_delay")
        if not self.human_contact_required:
            signals.append("human_contact_not_marked_required")
        return signals

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_id": self.service_id,
            "name": self.name,
            "responsible_entity": self.responsible_entity,
            "target_users": list(self.target_users),
            "required_documents": list(self.required_documents),
            "forms": list(self.forms),
            "channels": list(self.channels),
            "data_used": list(self.data_used),
            "appeal_or_review_path": self.appeal_or_review_path,
            "human_contact_required": self.human_contact_required,
            "oak_status": self.oak_status,
            "average_delay_days": self.average_delay_days,
            "document_burden": self.document_burden,
            "friction_signals": self.friction_signals(),
            "notes": self.notes,
            "metadata": dict(self.metadata),
        }


@dataclass
class ServiceCatalog:
    """Collection of PublicService records."""

    services: Dict[str, PublicService] = field(default_factory=dict)
    m_minus: List[str] = field(default_factory=list)

    def add(self, service: PublicService) -> None:
        errors = service.validate()
        if errors:
            raise ValueError("Invalid PublicService: " + "; ".join(errors))
        if service.service_id in self.services:
            self.m_minus.append(f"duplicate service ignored: {service.service_id}")
            raise ValueError(f"duplicate service_id: {service.service_id}")
        self.services[service.service_id] = service

    def friction_report(self) -> Dict[str, Any]:
        signals: Dict[str, List[str]] = {}
        for service in self.services.values():
            current = service.friction_signals()
            if current:
                signals[service.service_id] = current
        return {
            "service_count": len(self.services),
            "services_with_signals": signals,
            "m_minus": list(self.m_minus),
            "oak_note": "Friction signals support service review; they are not final performance judgments.",
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": "omega_gov_qc_t.service_catalog.v0",
            "services": [service.to_dict() for service in self.services.values()],
            "friction_report": self.friction_report(),
        }
