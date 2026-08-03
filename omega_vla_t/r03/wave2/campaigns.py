"""Reversible campaign addressing for the Wave 2 Operator Universe.

The codec exposes a large logical test frontier while materializing only finite,
explicitly requested plans. Frontier size is not a count of executed tests or
validated mathematical results.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import gcd
from typing import Any, Iterator

from .families import OperatorFamilyCatalog, default_family_catalog


class CampaignCodecError(ValueError):
    pass


_DIMENSIONS = (
    1, 2, 3, 4, 5, 8, 10, 12, 16, 20, 24, 32, 48, 64, 96, 128, 256, 512,
    "n", "large_n",
)
_REPRESENTATIONS = ("symbolic", "dense", "csr", "matrix_free", "hybrid")
_SCALAR_SYSTEMS = ("Q", "R", "C", "IR", "GF", "H")
_PROPERTY_QUESTIONS = (
    "linearity",
    "domain_codomain",
    "units",
    "self_adjoint",
    "skew_adjoint",
    "normal",
    "unitary",
    "projection",
    "positive_semidefinite",
    "positive_definite",
    "invertibility",
    "rank",
    "spectrum",
    "pseudospectrum",
    "commutant",
    "stability",
    "conditioning",
    "convergence",
    "conservation",
    "counterexample_search",
)
_BACKENDS = (
    "python_reference",
    "numpy",
    "scipy_sparse",
    "jax",
    "pytorch",
    "cpp_eigen",
    "rust_nalgebra",
    "rust_faer",
    "cuda",
    "lean4_target",
)
_CONDITION_REGIMES = (
    "well_conditioned",
    "moderate",
    "ill_conditioned",
    "near_singular",
    "singular",
    "defective",
    "repeated_spectrum",
    "nonnormal",
)
_SPARSITY_REGIMES = (
    "zero",
    "diagonal",
    "banded",
    "very_sparse",
    "sparse",
    "medium",
    "dense",
    "matrix_free",
)
_TOLERANCES = ("exact", "1e-14", "1e-12", "1e-10", "1e-8", "adaptive")
_APPLICATIONS = (
    "pure_math",
    "numerical_linear_algebra",
    "signals",
    "spectroscopy",
    "crystals",
    "materials",
    "fluids",
    "plasmas",
    "photonics",
    "quantum",
    "control",
    "AI",
    "reverse_engineering",
    "neuroscience",
    "batteries",
    "HGFM",
)
_METHODS = (
    "direct",
    "iterative",
    "Krylov",
    "spectral",
    "variational",
    "randomized",
    "interval",
    "symbolic",
    "SMT",
    "formal_target",
    "adversarial",
    "multi_precision",
)


@dataclass(frozen=True)
class OperatorCampaignAddress:
    family_id: str
    dimension: int | str
    representation: str
    scalar_system: str
    property_question: str
    backend: str
    condition_regime: str
    sparsity_regime: str
    tolerance: str
    application: str
    method: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def canonical(self) -> str:
        return "|".join(f"{key}={value}" for key, value in self.to_dict().items())

    def digest(self) -> str:
        return sha256(self.canonical().encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CampaignPlan:
    requested: int
    generated: int
    seed: int
    start_offset: int
    logical_frontier_size: int
    addresses: tuple[OperatorCampaignAddress, ...]
    aggregate_digest: str
    permanent_total_cap: None = None
    theorem_claimed: bool = False
    formal_proof_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class OperatorCampaignCodec:
    def __init__(self, catalog: OperatorFamilyCatalog | None = None) -> None:
        self.catalog = catalog or default_family_catalog()
        self.axes: tuple[tuple[str, tuple[Any, ...]], ...] = (
            ("family_id", tuple(value.family_id for value in self.catalog)),
            ("dimension", _DIMENSIONS),
            ("representation", _REPRESENTATIONS),
            ("scalar_system", _SCALAR_SYSTEMS),
            ("property_question", _PROPERTY_QUESTIONS),
            ("backend", _BACKENDS),
            ("condition_regime", _CONDITION_REGIMES),
            ("sparsity_regime", _SPARSITY_REGIMES),
            ("tolerance", _TOLERANCES),
            ("application", _APPLICATIONS),
            ("method", _METHODS),
        )
        self.radices = tuple(len(values) for _, values in self.axes)
        size = 1
        for radix in self.radices:
            size *= radix
        self.size = size

    def decode(self, index: int) -> OperatorCampaignAddress:
        if index < 0 or index >= self.size:
            raise IndexError(f"campaign index must be in [0, {self.size})")
        positions = [0] * len(self.radices)
        value = index
        for axis in range(len(self.radices) - 1, -1, -1):
            value, positions[axis] = divmod(value, self.radices[axis])
        payload = {
            name: values[position]
            for (name, values), position in zip(self.axes, positions)
        }
        return OperatorCampaignAddress(**payload)

    def encode(self, address: OperatorCampaignAddress) -> int:
        payload = address.to_dict()
        index = 0
        for name, values in self.axes:
            try:
                position = values.index(payload[name])
            except ValueError as exc:
                raise CampaignCodecError(
                    f"invalid value for {name}: {payload[name]!r}"
                ) from exc
            index = index * len(values) + position
        return index

    def iter_indices(
        self,
        count: int,
        *,
        seed: int = 0,
        start_offset: int = 0,
    ) -> Iterator[int]:
        if count < 0 or start_offset < 0:
            raise CampaignCodecError("count and start_offset cannot be negative")
        if start_offset + count > self.size:
            raise CampaignCodecError("requested range exceeds logical frontier")
        if count == 0:
            return
        start = int.from_bytes(
            sha256(f"start:{seed}".encode()).digest()[:16], "big"
        ) % self.size
        step = int.from_bytes(
            sha256(f"step:{seed}".encode()).digest()[:16], "big"
        ) % self.size
        step = max(step, 1)
        while gcd(step, self.size) != 1:
            step += 1
            if step >= self.size:
                step = 1
        for ordinal in range(start_offset, start_offset + count):
            yield (start + ordinal * step) % self.size

    def plan(
        self,
        count: int,
        *,
        seed: int = 0,
        start_offset: int = 0,
    ) -> CampaignPlan:
        addresses = tuple(
            self.decode(index)
            for index in self.iter_indices(
                count,
                seed=seed,
                start_offset=start_offset,
            )
        )
        aggregate = sha256(
            "".join(address.digest() for address in addresses).encode("ascii")
        ).hexdigest()
        return CampaignPlan(
            requested=count,
            generated=len(addresses),
            seed=seed,
            start_offset=start_offset,
            logical_frontier_size=self.size,
            addresses=addresses,
            aggregate_digest=aggregate,
        )

    def manifest(self) -> dict[str, Any]:
        return {
            "axes": {name: len(values) for name, values in self.axes},
            "axis_values": {
                name: list(values) if len(values) <= 32 else None
                for name, values in self.axes
            },
            "logical_frontier_size": self.size,
            "permanent_total_cap": None,
            "theorem_claimed": False,
            "formal_proof_claimed": False,
            "scientific_validation_claimed": False,
            "claim_boundary": (
                "logical addresses are plans; execution, proof and validation are separate"
            ),
        }

    def deterministic_digest(self) -> str:
        payload = json.dumps(self.manifest(), sort_keys=True, separators=(",", ":"))
        return sha256(payload.encode("utf-8")).hexdigest()
