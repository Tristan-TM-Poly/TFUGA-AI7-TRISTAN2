from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Mapping, Tuple

from .public_sources import get_public_source
from .r06_protocol import get_protocol


def _sha256_field(name: str, value: str) -> None:
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value.lower()):
        raise ValueError(f"{name} must be a 64-character SHA-256 digest")


@dataclass(frozen=True)
class EvidenceAssetRecord:
    """Post-acquisition identity/provenance record for one external asset."""

    source_id: str
    source_version: str
    asset_id: str
    resource_uri: str
    payload_sha256: str
    payload_bytes: int
    acquisition_plan_hash: str
    license_id: str
    citation: str
    variable_mapping_hash: str
    grouping_mapping_hash: str
    provenance_review_status: str
    license_review_status: str
    retrieval_date: str
    automatic_biological_promotion: bool = False

    def __post_init__(self) -> None:
        get_public_source(self.source_id)
        for name in (
            "source_version",
            "asset_id",
            "resource_uri",
            "license_id",
            "citation",
            "provenance_review_status",
            "license_review_status",
            "retrieval_date",
        ):
            if not getattr(self, name):
                raise ValueError(f"{name} must be non-empty")
        if self.payload_bytes < 0:
            raise ValueError("payload_bytes must be >= 0")
        for name in (
            "payload_sha256",
            "acquisition_plan_hash",
            "variable_mapping_hash",
            "grouping_mapping_hash",
        ):
            _sha256_field(name, getattr(self, name))
        if self.automatic_biological_promotion:
            raise ValueError("an evidence asset cannot promote a biological claim automatically")

    def canonical_dict(self) -> Mapping[str, object]:
        return asdict(self)

    def digest(self) -> str:
        text = json.dumps(self.canonical_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class EvidenceBundleRecord:
    """Bind immutable assets to one frozen hypothesis protocol and plan."""

    bundle_id: str
    hypothesis_id: str
    protocol_hash: str
    acquisition_plan_hash: str
    asset_record_hashes: Tuple[str, ...]
    variable_contract_hash: str
    split_contract_hash: str
    negative_control_contract_hash: str
    status: str = "EVIDENCE_PREPARED_NOT_CLAIM_PROMOTED"
    automatic_biological_promotion: bool = False

    def __post_init__(self) -> None:
        if not self.bundle_id or not self.asset_record_hashes:
            raise ValueError("bundle_id and asset_record_hashes must be non-empty")
        protocol = get_protocol(self.hypothesis_id)
        if protocol.digest() != self.protocol_hash:
            raise ValueError("bundle protocol_hash does not match executable preregistration")
        for name in (
            "protocol_hash",
            "acquisition_plan_hash",
            "variable_contract_hash",
            "split_contract_hash",
            "negative_control_contract_hash",
        ):
            _sha256_field(name, getattr(self, name))
        for digest in self.asset_record_hashes:
            _sha256_field("asset_record_hash", digest)
        if self.automatic_biological_promotion:
            raise ValueError("evidence preparation cannot automatically promote a biological claim")

    def canonical_dict(self) -> Mapping[str, object]:
        return asdict(self)

    def digest(self) -> str:
        text = json.dumps(self.canonical_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return sha256(text.encode("utf-8")).hexdigest()


def mapping_digest(mapping: Mapping[str, object]) -> str:
    """Hash a variable/group/split/control contract before model evaluation."""

    text = json.dumps(mapping, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(text.encode("utf-8")).hexdigest()
