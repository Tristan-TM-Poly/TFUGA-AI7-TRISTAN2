"""Static compatibility and epistemic gates for logical variants."""
from __future__ import annotations

from dataclasses import dataclass

from .model import AlgorithmSpec, VariantAddress


@dataclass(frozen=True, slots=True)
class GateDecision:
    accepted: bool
    reason: str | None
    warnings: tuple[str, ...] = ()


GPU_HARDWARES = {"nvidia-cuda", "amd-hip", "apple-gpu", "integrated-gpu"}
CPU_LANGUAGES = {"python", "c", "cpp", "rust"}
SPARSE_LAYOUTS = {"csr", "csc"}


def evaluate_static_gate(spec: AlgorithmSpec, variant: VariantAddress) -> GateDecision:
    warnings: list[str] = []
    if variant.language not in CPU_LANGUAGES:
        return GateDecision(False, "backend-not-implemented-r02")
    if variant.parallelism == "gpu" and variant.hardware not in GPU_HARDWARES:
        return GateDecision(False, "gpu-parallelism-requires-gpu-profile")
    if variant.hardware in GPU_HARDWARES and variant.parallelism not in {"gpu", "single"}:
        return GateDecision(False, "gpu-profile-incompatible-with-cpu-parallelism")
    if variant.layout in SPARSE_LAYOUTS and spec.family not in {"matrix", "tensor", "graph", "hypergraph"}:
        return GateDecision(False, "sparse-layout-not-justified-for-family")
    if variant.strategy == "in-place" and spec.operation in {"convolution", "correlation", "matmul", "svd", "eigen"}:
        return GateDecision(False, "in-place-dependency-proof-missing")
    if variant.precision in {"f16", "bf16"} and spec.dtype in {"int64", "complex128"}:
        return GateDecision(False, "precision-domain-mismatch")
    if variant.strategy == "simd-explicit" and variant.hardware in {"generic-cpu", "embedded", "unknown-future"}:
        return GateDecision(False, "explicit-simd-isa-not-resolved")
    if variant.parallelism == "distributed":
        warnings.append("distributed-cost-model-not-measured-r02")
    if variant.objective == "energy":
        warnings.append("energy-meter-not-implemented-r02")
    return GateDecision(True, None, tuple(warnings))
