from __future__ import annotations
import hashlib, json
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Mapping, Sequence


# --- hashutil ---
def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def sha256(value: Any) -> str:
    payload = value if isinstance(value, bytes) else canonical_json(value).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

def merkle_root(leaves: Iterable[str]) -> str:
    layer = [sha256({"leaf": leaf}) for leaf in leaves]
    if not layer:
        return sha256({"empty": True})
    while len(layer) > 1:
        if len(layer) % 2:
            layer.append(layer[-1])
        layer = [sha256({"left": layer[i], "right": layer[i + 1]}) for i in range(0, len(layer), 2)]
    return layer[0]


# --- models ---
@dataclass(frozen=True)
class SourceDescriptor:
    source_id: str
    title: str
    publisher: str
    source_kind: str
    canonical_ref: str
    licence_id: str
    update_cadence: str
    geographic_resolution: str
    temporal_resolution: str
    allowed_uses: Sequence[str]
    prohibited_uses: Sequence[str]
    sensitivity: str = "public"
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def descriptor_hash(self) -> str:
        return sha256(self.to_dict())

@dataclass(frozen=True)
class Observation:
    observation_id: str
    source_id: str
    variable: str
    value: float
    unit: str
    observed_at: str
    region_id: str
    quality_flag: str
    uncertainty: float
    method: str
    source_row: int
    sensitivity: str = "public"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def evidence_hash(self) -> str:
        return sha256(self.to_dict())

@dataclass(frozen=True)
class QuarantineRecord:
    row_number: int
    reason_codes: Sequence[str]
    raw_record: Mapping[str, Any]
    record_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass(frozen=True)
class IngestReceipt:
    receipt_id: str
    source_id: str
    input_format: str
    input_sha256: str
    accepted_count: int
    quarantined_count: int
    duplicate_count: int
    observation_merkle_root: str
    quarantine_merkle_root: str
    policy_hash: str
    deterministic: bool
    claims: Mapping[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass(frozen=True)
class Snapshot:
    snapshot_id: str
    created_at: str
    source_ids: Sequence[str]
    observation_ids: Sequence[str]
    observation_merkle_root: str
    parent_snapshot_id: str | None
    status: str
    evidence_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass(frozen=True)
class SnapshotDiff:
    before_snapshot_id: str
    after_snapshot_id: str
    added_observation_ids: Sequence[str]
    removed_observation_ids: Sequence[str]
    unchanged_count: int
    changed_series: Sequence[str]
    evidence_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass(frozen=True)
class Claim:
    claim_id: str
    statement: str
    subject: str
    predicate: str
    object_value: str
    scope: str
    valid_from: str
    valid_to: str | None
    status: str
    confidence: float
    evidence_ids: Sequence[str]
    counter_evidence_ids: Sequence[str]
    assumptions: Sequence[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def claim_hash(self) -> str:
        return sha256(self.to_dict())

@dataclass(frozen=True)
class Contradiction:
    contradiction_id: str
    claim_a: str
    claim_b: str
    kind: str
    severity: float
    explanation: str
    status: str = "OPEN_REVIEW"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass(frozen=True)
class SecurityAssessment:
    assessment_id: str
    source_ids: Sequence[str]
    precision_score: float
    linkage_score: float
    temporal_density_score: float
    infrastructure_specificity_score: float
    composability_risk: float
    decision: str
    reasons: Sequence[str]
    controls: Sequence[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass(frozen=True)
class ModelEstimate:
    model_id: str
    series_id: str
    estimate: float
    lower: float
    upper: float
    assumptions: Sequence[str]
    evidence_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass(frozen=True)
class ModelDisagreement:
    series_id: str
    estimates: Sequence[ModelEstimate]
    spread: float
    normalized_disagreement: float
    oak_status: str
    evidence_hash: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["estimates"] = [estimate.to_dict() for estimate in self.estimates]
        return data

@dataclass(frozen=True)
class CampaignReport:
    campaign_id: str
    source_count: int
    accepted_observations: int
    quarantined_observations: int
    snapshot: Snapshot
    claims: Sequence[Claim]
    contradictions: Sequence[Contradiction]
    security: SecurityAssessment
    model_disagreements: Sequence[ModelDisagreement]
    status: str
    claims_boundary: Mapping[str, bool]
    evidence_hash: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["snapshot"] = self.snapshot.to_dict()
        data["claims"] = [claim.to_dict() for claim in self.claims]
        data["contradictions"] = [item.to_dict() for item in self.contradictions]
        data["security"] = self.security.to_dict()
        data["model_disagreements"] = [item.to_dict() for item in self.model_disagreements]
        return data


# --- policy ---
@dataclass(frozen=True)
class PublicEvidencePolicy:
    policy_id: str = "omega-hqt-r02-public-evidence-policy"
    allowed_source_kinds: Sequence[str] = ("open_data_export", "public_report_extract", "synthetic_fixture")
    allowed_sensitivities: Sequence[str] = ("public", "public_aggregated")
    prohibited_fields: Sequence[str] = (
        "scada_tag",
        "relay_setting",
        "credential",
        "customer_account",
        "exact_substation_topology",
        "control_command",
        "private_personal_identifier",
    )
    maximum_input_bytes: int = 5_000_000
    maximum_rows: int = 100_000
    minimum_geographic_resolution: str = "regional"
    require_licence: bool = True
    require_offline_input: bool = True
    require_source_hash: bool = True
    permit_network_fetch: bool = False
    permit_operational_output: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def policy_hash(self) -> str:
        return sha256(self.to_dict())

def inspect_prohibited_fields(record: Mapping[str, Any], policy: PublicEvidencePolicy) -> list[str]:
    lower_keys = {str(key).lower() for key in record}
    return sorted(field for field in policy.prohibited_fields if field in lower_keys)


# --- licensing ---
@dataclass(frozen=True)
class LicenceDecision:
    licence_id: str
    allowed: bool
    reason: str
    required_attribution: Sequence[str]

KNOWN_PUBLIC_LICENCES = {
    "open-government-canada-2.0": (True, "Reuse allowed subject to attribution and licence terms."),
    "cc-by-4.0": (True, "Reuse allowed with attribution."),
    "cc0-1.0": (True, "Public-domain dedication; provenance still retained by OAK."),
    "synthetic-fixture": (True, "Repository-generated synthetic fixture."),
    "unknown": (False, "Unknown licence requires human review before ingestion."),
    "all-rights-reserved": (False, "No default reuse permission."),
}

def evaluate_licence(source: SourceDescriptor) -> LicenceDecision:
    allowed, reason = KNOWN_PUBLIC_LICENCES.get(
        source.licence_id,
        (False, "Licence is not in the explicit allow-list."),
    )
    attribution = (source.publisher, source.title, source.canonical_ref) if allowed else ()
    return LicenceDecision(source.licence_id, allowed, reason, attribution)


# --- source_catalog ---
def synthetic_source_catalog() -> tuple[SourceDescriptor, ...]:
    return (
        SourceDescriptor(
            source_id="fixture-demand-regional",
            title="Synthetic regional demand fixture",
            publisher="Ω-HQT Research Fixtures",
            source_kind="synthetic_fixture",
            canonical_ref="repo://fixtures/demand-regional-v2",
            licence_id="synthetic-fixture",
            update_cadence="static",
            geographic_resolution="regional",
            temporal_resolution="hourly",
            allowed_uses=("research", "testing", "benchmarking"),
            prohibited_uses=("operational_dispatch", "real_asset_inference"),
        ),
        SourceDescriptor(
            source_id="fixture-production-regional",
            title="Synthetic regional production fixture",
            publisher="Ω-HQT Research Fixtures",
            source_kind="synthetic_fixture",
            canonical_ref="repo://fixtures/production-regional-v2",
            licence_id="synthetic-fixture",
            update_cadence="static",
            geographic_resolution="regional",
            temporal_resolution="hourly",
            allowed_uses=("research", "testing", "benchmarking"),
            prohibited_uses=("operational_dispatch", "real_asset_inference"),
        ),
    )

def source_by_id(source_id: str) -> SourceDescriptor:
    for source in synthetic_source_catalog():
        if source.source_id == source_id:
            return source
    raise KeyError(source_id)
