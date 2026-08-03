"""Deterministic TensorProdLift-T specification compiler."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Mapping

from .models import canonical_json
from .projectors import dimension_identity


@dataclass(frozen=True)
class CompileResult:
    plan: Mapping[str, Any]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = {"plan": dict(self.plan), "warnings": list(self.warnings)}
        payload["sha256"] = sha256(canonical_json(payload).encode("utf-8")).hexdigest()
        return payload


def compile_spec(spec: Mapping[str, Any]) -> CompileResult:
    left_dim = int(spec.get("left_dimension", 0))
    right_dim = int(spec.get("right_dimension", 0))
    if left_dim <= 0 or right_dim <= 0:
        raise ValueError("left_dimension and right_dimension must be positive")

    square = left_dim == right_dim
    preserve_inputs = bool(spec.get("preserve_inputs", True))
    exact_reconstruction = bool(spec.get("exact_reconstruction", True))
    requested = tuple(str(item) for item in spec.get("channels", ("full",)))
    warnings: list[str] = []

    known = {
        "full",
        "carrier",
        "symmetric",
        "symmetric_traceless",
        "trace",
        "antisymmetric",
        "blocks",
        "residual",
    }
    unknown = sorted(set(requested) - known)
    if unknown:
        warnings.append(f"unknown channels retained as unresolved requests: {unknown}")
    if not square and any(
        name in requested for name in ("symmetric", "symmetric_traceless", "trace", "antisymmetric")
    ):
        warnings.append(
            "transpose/trace channels require an identified isomorphism or square tensor; they are disabled"
        )

    channels: list[dict[str, Any]] = []
    if "full" in requested:
        channels.append({"name": "full", "dimension": left_dim * right_dim, "exact": True})
    if preserve_inputs or "carrier" in requested:
        channels.append(
            {
                "name": "carrier",
                "dimension": left_dim + right_dim,
                "exact": True,
                "independence": "input-state, not extra bilinear rank",
            }
        )
    if square:
        dims = dimension_identity(left_dim)
        for name in ("symmetric", "symmetric_traceless", "trace", "antisymmetric"):
            if name in requested:
                channels.append({"name": name, "dimension": dims[name], "exact": True})
    if "residual" in requested or exact_reconstruction:
        channels.append(
            {
                "name": "residual",
                "dimension": left_dim * right_dim,
                "exact": True,
                "semantic": "zero for exact transforms; explicit for approximations",
            }
        )

    plan = {
        "schema_version": "omega.tensor.repair.compile-plan.v1",
        "operation": "TensorProdLift-T",
        "left_dimension": left_dim,
        "right_dimension": right_dim,
        "classical_tensor_dimension": left_dim * right_dim,
        "carrier_dimension": left_dim + right_dim,
        "square": square,
        "channels": channels,
        "requested_channels": list(requested),
        "exact_reconstruction_required": exact_reconstruction,
        "oak_gates": [
            "classical-dimension",
            "dimension-branching",
            "analysis-synthesis-roundtrip",
            "residual-ledger",
            "epistemic-boundary",
        ],
        "claims": {
            "dimensions_created_for_free": False,
            "all_views_independent": False,
            "universal_compression_claimed": False,
            "new_physical_law_claimed": False,
        },
    }
    return CompileResult(plan, tuple(warnings))
