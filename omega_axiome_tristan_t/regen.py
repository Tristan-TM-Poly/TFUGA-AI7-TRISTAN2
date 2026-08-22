"""BOOK0 regeneration primitives for Ω-AXIOME-TRISTAN."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .core import AxiomGenome, canonical_json, genome_to_dict, stable_digest


@dataclass(frozen=True)
class Book0Manifest:
    kernel_version: str
    primitives: tuple[str, ...]
    invariants: tuple[str, ...]
    required_probes: tuple[str, ...]

    def digest(self) -> str:
        return stable_digest(asdict(self))


@dataclass(frozen=True)
class RegenerationReceipt:
    seed_digest: str
    rebuilt_digest: str
    behavioral_probe_results: dict[str, bool]
    epsilon_residual: int
    equivalent_relative_to_probes: bool
    authoritative: bool = False


DEFAULT_BOOK0 = Book0Manifest(
    kernel_version="0.1.0",
    primitives=("OBSERVE", "REPRESENT", "CLAIM", "CONTRAST", "PROBE", "VERIFY", "REMEMBER", "REGENERATE"),
    invariants=(
        "GENERATED_NE_VERIFIED",
        "MODEL_NE_REALITY",
        "SIMULATION_NE_EXPERIMENT",
        "GENERATOR_NE_JUDGE",
        "CLAIM_SCOPE_LE_EVIDENCE_SCOPE",
        "REVENUE_NE_TRUTH",
        "CAPABILITY_NE_AUTHORITY",
    ),
    required_probes=("CAN_SERIALIZE", "CAN_REPLAY", "CAN_COMPARE", "CAN_AUDIT"),
)


def regeneration_receipt(genome: AxiomGenome, probes: dict[str, bool] | None = None) -> RegenerationReceipt:
    payload = genome_to_dict(genome)
    seed_digest = stable_digest(payload)
    serialized = canonical_json(payload)
    rebuilt_payload: Any = __import__("json").loads(serialized)
    rebuilt_digest = stable_digest(rebuilt_payload)
    probe_results = probes or {
        "CAN_SERIALIZE": True,
        "CAN_REPLAY": rebuilt_digest == seed_digest,
        "CAN_COMPARE": True,
        "CAN_AUDIT": True,
    }
    missing = set(DEFAULT_BOOK0.required_probes) - set(probe_results)
    equivalent = not missing and all(bool(probe_results[p]) for p in DEFAULT_BOOK0.required_probes) and seed_digest == rebuilt_digest
    return RegenerationReceipt(
        seed_digest=seed_digest,
        rebuilt_digest=rebuilt_digest,
        behavioral_probe_results=dict(probe_results),
        epsilon_residual=0 if seed_digest == rebuilt_digest else 1,
        equivalent_relative_to_probes=equivalent,
        authoritative=False,
    )
