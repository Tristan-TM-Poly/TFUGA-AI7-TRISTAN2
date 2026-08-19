from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class CandidateStatus(str, Enum):
    CANDIDATE = "candidate"
    FILTERED_COMPOSITE = "filtered_composite"
    PROBABLE_PRIME = "probable_prime"
    PROVEN_PRIME = "proven_prime"
    VERIFIED_PRIME = "verified_prime"


@dataclass(frozen=True, slots=True)
class PrimeCandidate:
    value: int
    family: str
    parameters: dict[str, int | str]
    status: CandidateStatus = CandidateStatus.CANDIDATE
    small_factor: int | None = None
    witness: int | None = None
    notes: tuple[str, ...] = ()

    @property
    def bit_length(self) -> int:
        return self.value.bit_length()

    @property
    def decimal_digits(self) -> int:
        return len(str(self.value))

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        payload["bit_length"] = self.bit_length
        payload["decimal_digits"] = self.decimal_digits
        return payload


@dataclass(frozen=True, slots=True)
class NTTProfile:
    modulus: int
    two_adicity: int
    primitive_root: int
    root_of_unity: int
    maximum_transform_length: int

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class MarketScore:
    total: float
    utility: float
    proof_quality: float
    rarity: float
    implementation: float
    provenance: float
    cost_penalty: float
    risk_penalty: float
    classification: str

    def to_dict(self) -> dict[str, float | str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PrimeCertificate:
    certificate_version: str
    certificate_id: str
    candidate: dict[str, Any]
    proof: dict[str, Any]
    verification: dict[str, Any]
    applications: list[str]
    market_score: dict[str, Any]
    provenance: dict[str, Any]
    oak: dict[str, Any]
    sha256: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CampaignReport:
    policy: dict[str, Any]
    candidates_examined: int = 0
    filtered_composites: int = 0
    probable_primes: int = 0
    proven_primes: int = 0
    certificates: list[PrimeCertificate] = field(default_factory=list)
    negative_memory: list[dict[str, Any]] = field(default_factory=list)
    hypergraph: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy": self.policy,
            "candidates_examined": self.candidates_examined,
            "filtered_composites": self.filtered_composites,
            "probable_primes": self.probable_primes,
            "proven_primes": self.proven_primes,
            "certificates": [item.to_dict() for item in self.certificates],
            "negative_memory": self.negative_memory,
            "hypergraph": self.hypergraph,
        }
