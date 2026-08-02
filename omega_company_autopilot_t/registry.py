"""Company and division registry with constrained legal-state transitions."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .models import CompanyRecord, CompanyState, DivisionRecord, EvidenceRef
from .serialization import load_company, save_company


_ALLOWED_TRANSITIONS: dict[CompanyState, set[CompanyState]] = {
    CompanyState.IDEA: {CompanyState.CANDIDATE_LEGAL_ENTITY, CompanyState.M_MINUS_HOLD},
    CompanyState.CANDIDATE_LEGAL_ENTITY: {CompanyState.PROFESSIONAL_REVIEW, CompanyState.M_MINUS_HOLD},
    CompanyState.PROFESSIONAL_REVIEW: {CompanyState.FILING_READY, CompanyState.CANDIDATE_LEGAL_ENTITY, CompanyState.M_MINUS_HOLD},
    CompanyState.FILING_READY: {CompanyState.FILING_SUBMITTED, CompanyState.PROFESSIONAL_REVIEW, CompanyState.M_MINUS_HOLD},
    CompanyState.FILING_SUBMITTED: {CompanyState.REGISTERED, CompanyState.INCORPORATED, CompanyState.PROFESSIONAL_REVIEW, CompanyState.M_MINUS_HOLD},
    CompanyState.REGISTERED: {CompanyState.POST_FORMATION, CompanyState.M_MINUS_HOLD},
    CompanyState.INCORPORATED: {CompanyState.POST_FORMATION, CompanyState.M_MINUS_HOLD},
    CompanyState.POST_FORMATION: {CompanyState.OPERATING, CompanyState.M_MINUS_HOLD},
    CompanyState.OPERATING: {CompanyState.PRODUCTION_AUTHORIZED, CompanyState.M_MINUS_HOLD},
    CompanyState.PRODUCTION_AUTHORIZED: {CompanyState.OPERATING, CompanyState.M_MINUS_HOLD},
    CompanyState.M_MINUS_HOLD: {
        CompanyState.CANDIDATE_LEGAL_ENTITY,
        CompanyState.PROFESSIONAL_REVIEW,
        CompanyState.FILING_READY,
        CompanyState.POST_FORMATION,
        CompanyState.OPERATING,
    },
}


class RegistryError(ValueError):
    pass


class CompanyRegistry:
    def __init__(self, company: CompanyRecord) -> None:
        self.company = company

    @classmethod
    def load(cls, path: Path) -> "CompanyRegistry":
        return cls(load_company(path))

    def save(self, path: Path) -> None:
        self.company.touch()
        save_company(self.company, path)

    def transition(self, target: CompanyState, *, evidence: Iterable[EvidenceRef] = ()) -> CompanyRecord:
        current = self.company.state
        if target == current:
            return self.company
        if target not in _ALLOWED_TRANSITIONS[current]:
            raise RegistryError(f"illegal_transition:{current.value}->{target.value}")
        supplied = list(evidence)
        self._validate_transition(target, supplied)
        self.company.state = target
        self.company.evidence.extend(supplied)
        self.company.touch()
        return self.company

    def _validate_transition(self, target: CompanyState, evidence: list[EvidenceRef]) -> None:
        verified_kinds = {item.kind for item in [*self.company.evidence, *evidence] if item.verified}
        if target in {CompanyState.REGISTERED, CompanyState.INCORPORATED}:
            if not self.company.legal_name:
                raise RegistryError("legal_name_required")
            required = "registry_snapshot" if target is CompanyState.REGISTERED else "certificate_of_incorporation"
            if required not in verified_kinds:
                raise RegistryError(f"verified_{required}_required")
        if target is CompanyState.POST_FORMATION and not self.company.legal_identity_verified:
            raise RegistryError("legal_identity_verification_required")
        if target is CompanyState.OPERATING:
            if not self.company.privacy_officer:
                raise RegistryError("privacy_officer_required")
            if not self.company.directors:
                raise RegistryError("director_required")
        if target is CompanyState.PRODUCTION_AUTHORIZED:
            if not self.company.production_enabled:
                raise RegistryError("production_enabled_flag_required")
            if not self.company.registry_snapshot_verified:
                raise RegistryError("registry_snapshot_verification_required")

    def add_division(self, division: DivisionRecord) -> None:
        if any(item.division_id == division.division_id for item in self.company.divisions):
            raise RegistryError(f"duplicate_division:{division.division_id}")
        division.owner_company_id = self.company.company_id
        self.company.divisions.append(division)
        self.company.touch()

    def disable_division(self, division_id: str) -> None:
        division = self.company.division(division_id)
        division.enabled = False
        self.company.touch()

    def set_legal_identifiers(self, *, legal_name: str, legal_form: str, incorporation_number: str | None = None, neq: str | None = None, cra_business_number: str | None = None) -> None:
        if not legal_name.strip():
            raise RegistryError("legal_name_blank")
        self.company.legal_name = legal_name.strip()
        self.company.legal_form = legal_form.strip()
        self.company.incorporation_number = incorporation_number or None
        self.company.neq = neq or None
        self.company.cra_business_number = cra_business_number or None
        self.company.touch()

    def verified_evidence(self, kind: str) -> list[EvidenceRef]:
        return [item for item in self.company.evidence if item.kind == kind and item.verified]
