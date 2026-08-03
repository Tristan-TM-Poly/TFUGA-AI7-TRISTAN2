from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable, Iterator, Mapping, Sequence

from .canonical import CanonicalizationError, canonical_hash
from .consent import ConsentBasis, ConsentScope, ConsentState
from .contacts import ContactState, RoleCategory
from .identity import IdentityState
from .opportunities import CompanyUnit, OpportunityState, OpportunityType
from .organizations import OrganizationType, RelationshipState


class RiskClass(str, Enum):
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    LEGAL = "legal"
    FINANCIAL = "financial"
    PRIVACY = "privacy"
    REPUTATION = "reputation"


class AuthorityLevel(str, Enum):
    PREPARE_ONLY = "prepare_only"
    LOW_RISK_POLICY = "low_risk_policy"
    FOUNDER_APPROVAL = "founder_approval"
    DUAL_APPROVAL = "dual_approval"
    PROFESSIONAL_REVIEW = "professional_review"
    EXTERNAL_PROVIDER_CONFIRMATION = "external_provider_confirmation"


class ExpectedDecision(str, Enum):
    ALLOW_PREPARATION = "allow_preparation"
    REQUIRE_EVIDENCE = "require_evidence"
    REQUIRE_CONSENT = "require_consent"
    REQUIRE_HUMAN_APPROVAL = "require_human_approval"
    REQUIRE_DUAL_APPROVAL = "require_dual_approval"
    REQUIRE_PROFESSIONAL_REVIEW = "require_professional_review"
    WAIT = "wait"
    BLOCK = "block"


@dataclass(frozen=True, slots=True)
class ScenarioDimensions:
    company_unit: CompanyUnit
    organization_type: OrganizationType
    opportunity_type: OpportunityType
    identity_state: IdentityState
    organization_state: RelationshipState
    contact_state: ContactState
    role_category: RoleCategory
    consent_basis: ConsentBasis
    consent_scope: ConsentScope
    consent_state: ConsentState
    opportunity_state: OpportunityState
    risk_class: RiskClass
    authority_level: AuthorityLevel
    evidence_band: int
    strategic_score_band: int

    def __post_init__(self) -> None:
        if self.evidence_band not in {0, 1, 2, 3, 4}:
            raise CanonicalizationError("evidence_band must be between 0 and 4")
        if self.strategic_score_band not in {0, 1, 2, 3, 4}:
            raise CanonicalizationError("strategic_score_band must be between 0 and 4")

    @property
    def scenario_key(self) -> str:
        return canonical_hash(self)


@dataclass(frozen=True, slots=True)
class ScenarioExpectation:
    decision: ExpectedDecision
    reasons: tuple[str, ...]
    requires_event: bool
    requires_external_execution: bool
    expected_company: CompanyUnit

    @property
    def expectation_hash(self) -> str:
        return canonical_hash(self)


@dataclass(frozen=True, slots=True)
class OakScenario:
    scenario_id: str
    dimensions: ScenarioDimensions
    expectation: ScenarioExpectation
    generator_version: str = "1.0"

    @property
    def scenario_hash(self) -> str:
        return canonical_hash(self)

    def as_mapping(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "dimensions": {
                key: value.value if isinstance(value, Enum) else value
                for key, value in self.dimensions.__dict__.items()
            },
            "expectation": {
                "decision": self.expectation.decision.value,
                "reasons": list(self.expectation.reasons),
                "requires_event": self.expectation.requires_event,
                "requires_external_execution": self.expectation.requires_external_execution,
                "expected_company": self.expectation.expected_company.value,
            },
            "generator_version": self.generator_version,
            "scenario_hash": self.scenario_hash,
        }


_COMPANY_ROUTES: Mapping[OpportunityType, CompanyUnit] = {
    OpportunityType.ENTREPRENEURSHIP_PROGRAM: CompanyUnit.PARENT,
    OpportunityType.FINANCING_PROGRAM: CompanyUnit.PARENT,
    OpportunityType.STRATEGIC_PARTNERSHIP: CompanyUnit.PARENT,
    OpportunityType.GRANT: CompanyUnit.PARENT,
    OpportunityType.REFERRAL: CompanyUnit.PARENT,
    OpportunityType.AUDIT_SERVICE: CompanyUnit.OAK,
    OpportunityType.SECURITY_REVIEW: CompanyUnit.OAK,
    OpportunityType.SOFTWARE_PILOT: CompanyUnit.SOFTWARE,
    OpportunityType.INTEGRATION: CompanyUnit.SOFTWARE,
    OpportunityType.LICENSING: CompanyUnit.SOFTWARE,
    OpportunityType.PROCUREMENT: CompanyUnit.SOFTWARE,
    OpportunityType.RESEARCH_PILOT: CompanyUnit.RESEARCH,
    OpportunityType.DATA_PARTNERSHIP: CompanyUnit.RESEARCH,
    OpportunityType.PUBLICATION: CompanyUnit.RESEARCH,
    OpportunityType.OPEN_SOURCE_COLLABORATION: CompanyUnit.RESEARCH,
    OpportunityType.ADVISORY: CompanyUnit.RESEARCH,
}


def theoretical_cardinality() -> int:
    dimensions = (
        len(CompanyUnit),
        len(OrganizationType),
        len(OpportunityType),
        len(IdentityState),
        len(RelationshipState),
        len(ContactState),
        len(RoleCategory),
        len(ConsentBasis),
        len(ConsentScope),
        len(ConsentState),
        len(OpportunityState),
        len(RiskClass),
        len(AuthorityLevel),
        5,
        5,
    )
    result = 1
    for value in dimensions:
        result *= value
    return result


def expected_company(opportunity_type: OpportunityType) -> CompanyUnit:
    return _COMPANY_ROUTES[opportunity_type]


def decide(dimensions: ScenarioDimensions) -> ScenarioExpectation:
    reasons: list[str] = []
    routed_company = expected_company(dimensions.opportunity_type)
    if dimensions.company_unit is not routed_company:
        return ScenarioExpectation(
            decision=ExpectedDecision.BLOCK,
            reasons=("opportunity routed to wrong company",),
            requires_event=True,
            requires_external_execution=False,
            expected_company=routed_company,
        )
    if dimensions.contact_state in {ContactState.SUPPRESSED, ContactState.BOUNCED}:
        return ScenarioExpectation(
            decision=ExpectedDecision.BLOCK,
            reasons=("contact is suppressed or bounced",),
            requires_event=True,
            requires_external_execution=False,
            expected_company=routed_company,
        )
    if dimensions.consent_state in {
        ConsentState.WITHDRAWN,
        ConsentState.DENIED,
        ConsentState.SUPPRESSED,
        ConsentState.EXPIRED,
    }:
        return ScenarioExpectation(
            decision=ExpectedDecision.BLOCK,
            reasons=("consent is not active",),
            requires_event=True,
            requires_external_execution=False,
            expected_company=routed_company,
        )
    if dimensions.consent_state is ConsentState.UNKNOWN or dimensions.consent_basis is ConsentBasis.NONE:
        return ScenarioExpectation(
            decision=ExpectedDecision.REQUIRE_CONSENT,
            reasons=("consent basis is absent or unknown",),
            requires_event=False,
            requires_external_execution=False,
            expected_company=routed_company,
        )
    if dimensions.risk_class in {RiskClass.LEGAL, RiskClass.FINANCIAL}:
        if dimensions.authority_level is not AuthorityLevel.PROFESSIONAL_REVIEW:
            return ScenarioExpectation(
                decision=ExpectedDecision.REQUIRE_PROFESSIONAL_REVIEW,
                reasons=("legal or financial risk requires professional review",),
                requires_event=False,
                requires_external_execution=False,
                expected_company=routed_company,
            )
    if dimensions.risk_class in {RiskClass.HIGH, RiskClass.PRIVACY, RiskClass.REPUTATION}:
        if dimensions.authority_level not in {
            AuthorityLevel.DUAL_APPROVAL,
            AuthorityLevel.PROFESSIONAL_REVIEW,
        }:
            return ScenarioExpectation(
                decision=ExpectedDecision.REQUIRE_DUAL_APPROVAL,
                reasons=("high-risk scenario requires independent approvals",),
                requires_event=False,
                requires_external_execution=False,
                expected_company=routed_company,
            )
    if dimensions.identity_state in {IdentityState.CONCEPT, IdentityState.INTERNAL_ROLE}:
        if dimensions.authority_level is not AuthorityLevel.PREPARE_ONLY:
            reasons.append("identity state permits preparation but not corporate execution")
            return ScenarioExpectation(
                decision=ExpectedDecision.ALLOW_PREPARATION,
                reasons=tuple(reasons),
                requires_event=True,
                requires_external_execution=False,
                expected_company=routed_company,
            )
    if dimensions.evidence_band <= 1:
        return ScenarioExpectation(
            decision=ExpectedDecision.REQUIRE_EVIDENCE,
            reasons=("evidence band is insufficient",),
            requires_event=False,
            requires_external_execution=False,
            expected_company=routed_company,
        )
    if dimensions.opportunity_state in {
        OpportunityState.WAITING,
        OpportunityState.ARCHIVED,
        OpportunityState.LOST,
    }:
        return ScenarioExpectation(
            decision=ExpectedDecision.WAIT,
            reasons=("opportunity state is not active",),
            requires_event=False,
            requires_external_execution=False,
            expected_company=routed_company,
        )
    if dimensions.strategic_score_band <= 1:
        return ScenarioExpectation(
            decision=ExpectedDecision.WAIT,
            reasons=("strategic score is below action threshold",),
            requires_event=False,
            requires_external_execution=False,
            expected_company=routed_company,
        )
    if dimensions.authority_level in {
        AuthorityLevel.PREPARE_ONLY,
        AuthorityLevel.LOW_RISK_POLICY,
    }:
        return ScenarioExpectation(
            decision=ExpectedDecision.REQUIRE_HUMAN_APPROVAL,
            reasons=("external action exceeds automatic authority",),
            requires_event=False,
            requires_external_execution=False,
            expected_company=routed_company,
        )
    return ScenarioExpectation(
        decision=ExpectedDecision.REQUIRE_HUMAN_APPROVAL,
        reasons=("qualified scenario may proceed only after exact human approval",),
        requires_event=True,
        requires_external_execution=True,
        expected_company=routed_company,
    )


def _choice(sequence: Sequence[Any], index: int, salt: int) -> Any:
    return sequence[(index * salt + salt * salt) % len(sequence)]


def generate_scenarios(
    *,
    count: int = 8192,
    seed: int = 20260802,
    generator_version: str = "1.0",
) -> Iterator[OakScenario]:
    if count < 1:
        raise CanonicalizationError("scenario count must be positive")
    rng = random.Random(seed)
    companies = tuple(CompanyUnit)
    organization_types = tuple(OrganizationType)
    opportunity_types = tuple(OpportunityType)
    identity_states = tuple(IdentityState)
    organization_states = tuple(RelationshipState)
    contact_states = tuple(ContactState)
    roles = tuple(RoleCategory)
    consent_bases = tuple(ConsentBasis)
    consent_scopes = tuple(ConsentScope)
    consent_states = tuple(ConsentState)
    opportunity_states = tuple(OpportunityState)
    risks = tuple(RiskClass)
    authority_levels = tuple(AuthorityLevel)
    seen_hashes: set[str] = set()
    generated = 0
    attempts = 0
    while generated < count:
        index = attempts
        attempts += 1
        opportunity_type = _choice(opportunity_types, index, 7)
        routed_company = expected_company(opportunity_type)
        company = routed_company if index % 5 else _choice(companies, index, 11)
        dimensions = ScenarioDimensions(
            company_unit=company,
            organization_type=_choice(organization_types, index, 13),
            opportunity_type=opportunity_type,
            identity_state=_choice(identity_states, index, 17),
            organization_state=_choice(organization_states, index, 19),
            contact_state=_choice(contact_states, index, 23),
            role_category=_choice(roles, index, 29),
            consent_basis=_choice(consent_bases, index, 31),
            consent_scope=_choice(consent_scopes, index, 37),
            consent_state=_choice(consent_states, index, 41),
            opportunity_state=_choice(opportunity_states, index, 43),
            risk_class=_choice(risks, index, 47),
            authority_level=_choice(authority_levels, index, 53),
            evidence_band=(index * 3 + rng.randrange(5)) % 5,
            strategic_score_band=(index * 4 + rng.randrange(5)) % 5,
        )
        if dimensions.scenario_key in seen_hashes:
            continue
        seen_hashes.add(dimensions.scenario_key)
        expectation = decide(dimensions)
        yield OakScenario(
            scenario_id=f"SCENARIO-{generated + 1:08d}",
            dimensions=dimensions,
            expectation=expectation,
            generator_version=generator_version,
        )
        generated += 1


def scenario_manifest(scenarios: Iterable[OakScenario], *, seed: int) -> dict[str, Any]:
    materialized = tuple(scenarios)
    counts: dict[str, int] = {}
    for scenario in materialized:
        key = scenario.expectation.decision.value
        counts[key] = counts.get(key, 0) + 1
    hashes = [scenario.scenario_hash for scenario in materialized]
    return {
        "schema_version": "1.0",
        "generator": "omega_company_outreach_t.foundation.scenario_atlas",
        "seed": seed,
        "scenario_count": len(materialized),
        "theoretical_cardinality": theoretical_cardinality(),
        "decision_counts": dict(sorted(counts.items())),
        "first_hash": hashes[0] if hashes else None,
        "last_hash": hashes[-1] if hashes else None,
        "ordered_scenario_hash": canonical_hash(hashes),
    }


def audit_scenarios(scenarios: Iterable[OakScenario]) -> list[str]:
    materialized = tuple(scenarios)
    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_dimension_hashes: set[str] = set()
    decisions: set[ExpectedDecision] = set()
    companies: set[CompanyUnit] = set()
    opportunity_types: set[OpportunityType] = set()
    risk_classes: set[RiskClass] = set()
    for scenario in materialized:
        if scenario.scenario_id in seen_ids:
            errors.append(f"duplicate scenario_id: {scenario.scenario_id}")
        seen_ids.add(scenario.scenario_id)
        if scenario.dimensions.scenario_key in seen_dimension_hashes:
            errors.append(f"duplicate scenario dimensions: {scenario.scenario_id}")
        seen_dimension_hashes.add(scenario.dimensions.scenario_key)
        expected = decide(scenario.dimensions)
        if expected.expectation_hash != scenario.expectation.expectation_hash:
            errors.append(f"expectation drift: {scenario.scenario_id}")
        decisions.add(scenario.expectation.decision)
        companies.add(scenario.dimensions.company_unit)
        opportunity_types.add(scenario.dimensions.opportunity_type)
        risk_classes.add(scenario.dimensions.risk_class)
    missing_decisions = set(ExpectedDecision) - decisions
    if missing_decisions:
        errors.append(f"scenario atlas missing decisions: {sorted(item.value for item in missing_decisions)}")
    missing_companies = set(CompanyUnit) - companies
    if missing_companies:
        errors.append(f"scenario atlas missing companies: {sorted(item.value for item in missing_companies)}")
    missing_opportunities = set(OpportunityType) - opportunity_types
    if missing_opportunities:
        errors.append(
            f"scenario atlas missing opportunity types: {sorted(item.value for item in missing_opportunities)}"
        )
    missing_risks = set(RiskClass) - risk_classes
    if missing_risks:
        errors.append(f"scenario atlas missing risks: {sorted(item.value for item in missing_risks)}")
    return errors


def write_atlas(
    directory: Path,
    *,
    count: int = 8192,
    seed: int = 20260802,
    shard_size: int = 512,
) -> dict[str, Any]:
    if shard_size < 1:
        raise CanonicalizationError("shard_size must be positive")
    scenarios = tuple(generate_scenarios(count=count, seed=seed))
    errors = audit_scenarios(scenarios)
    if errors:
        raise CanonicalizationError("scenario atlas audit failed: " + "; ".join(errors))
    directory.mkdir(parents=True, exist_ok=True)
    for index in range(0, len(scenarios), shard_size):
        shard = scenarios[index : index + shard_size]
        shard_path = directory / f"scenarios-{index // shard_size:04d}.jsonl"
        shard_path.write_text(
            "\n".join(json.dumps(item.as_mapping(), ensure_ascii=False, sort_keys=True) for item in shard)
            + "\n",
            encoding="utf-8",
        )
    manifest = scenario_manifest(scenarios, seed=seed)
    manifest.update(
        {
            "shard_size": shard_size,
            "shard_count": (len(scenarios) + shard_size - 1) // shard_size,
        }
    )
    (directory / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2),
        encoding="utf-8",
    )
    return manifest


def read_atlas(directory: Path) -> tuple[OakScenario, ...]:
    scenarios: list[OakScenario] = []
    for path in sorted(directory.glob("scenarios-*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            dimensions_payload = payload["dimensions"]
            expectation_payload = payload["expectation"]
            dimensions = ScenarioDimensions(
                company_unit=CompanyUnit(dimensions_payload["company_unit"]),
                organization_type=OrganizationType(dimensions_payload["organization_type"]),
                opportunity_type=OpportunityType(dimensions_payload["opportunity_type"]),
                identity_state=IdentityState(dimensions_payload["identity_state"]),
                organization_state=RelationshipState(dimensions_payload["organization_state"]),
                contact_state=ContactState(dimensions_payload["contact_state"]),
                role_category=RoleCategory(dimensions_payload["role_category"]),
                consent_basis=ConsentBasis(dimensions_payload["consent_basis"]),
                consent_scope=ConsentScope(dimensions_payload["consent_scope"]),
                consent_state=ConsentState(dimensions_payload["consent_state"]),
                opportunity_state=OpportunityState(dimensions_payload["opportunity_state"]),
                risk_class=RiskClass(dimensions_payload["risk_class"]),
                authority_level=AuthorityLevel(dimensions_payload["authority_level"]),
                evidence_band=int(dimensions_payload["evidence_band"]),
                strategic_score_band=int(dimensions_payload["strategic_score_band"]),
            )
            expectation = ScenarioExpectation(
                decision=ExpectedDecision(expectation_payload["decision"]),
                reasons=tuple(expectation_payload["reasons"]),
                requires_event=bool(expectation_payload["requires_event"]),
                requires_external_execution=bool(
                    expectation_payload["requires_external_execution"]
                ),
                expected_company=CompanyUnit(expectation_payload["expected_company"]),
            )
            scenario = OakScenario(
                scenario_id=str(payload["scenario_id"]),
                dimensions=dimensions,
                expectation=expectation,
                generator_version=str(payload.get("generator_version", "1.0")),
            )
            if payload.get("scenario_hash") != scenario.scenario_hash:
                raise CanonicalizationError(f"scenario hash mismatch: {scenario.scenario_id}")
            scenarios.append(scenario)
    return tuple(scenarios)


def audit_atlas_directory(directory: Path) -> dict[str, Any]:
    scenarios = read_atlas(directory)
    errors = audit_scenarios(scenarios)
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    regenerated = scenario_manifest(scenarios, seed=int(manifest["seed"]))
    for key in (
        "scenario_count",
        "theoretical_cardinality",
        "decision_counts",
        "first_hash",
        "last_hash",
        "ordered_scenario_hash",
    ):
        if manifest.get(key) != regenerated.get(key):
            errors.append(f"manifest mismatch for {key}")
    return {
        "valid": not errors,
        "errors": errors,
        "scenario_count": len(scenarios),
        "manifest_hash": canonical_hash(manifest),
    }
