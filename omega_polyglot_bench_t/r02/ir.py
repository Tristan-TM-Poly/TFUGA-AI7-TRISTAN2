"""Small, auditable kernel IR and proof-obligation derivation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class IRNode:
    op: str
    args: tuple[Any, ...] = ()
    attrs: tuple[tuple[str, Any], ...] = ()

    def attr_map(self) -> dict[str, Any]:
        return dict(self.attrs)


@dataclass(frozen=True, slots=True)
class KernelIR:
    kernel_id: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    body: tuple[IRNode, ...]
    invariants: tuple[str, ...] = ()
    metadata: tuple[tuple[str, Any], ...] = ()

    def validate(self) -> None:
        if not self.kernel_id:
            raise ValueError("kernel_id is required")
        if not self.outputs:
            raise ValueError("at least one output is required")
        defined = set(self.inputs)
        for node in self.body:
            if node.op == "assign":
                attrs = node.attr_map()
                target = attrs.get("target")
                if not target:
                    raise ValueError("assign node requires target")
                defined.add(str(target))
            elif node.op not in {"loop", "binary", "unary", "reduce", "call", "return", "load", "store", "constant"}:
                raise ValueError(f"unsupported IR operation: {node.op}")
        if not set(self.outputs).issubset(defined):
            raise ValueError("all outputs must be defined")


def affine_vector_ir() -> KernelIR:
    ir = KernelIR(
        kernel_id="vector_affine_f64",
        inputs=("x", "y", "scalar", "length"),
        outputs=("output",),
        body=(
            IRNode("loop", attrs=(("index", "i"), ("start", 0), ("stop", "length"))),
            IRNode("load", args=("x", "i"), attrs=(("name", "xi"),)),
            IRNode("load", args=("y", "i"), attrs=(("name", "yi"),)),
            IRNode("binary", args=("scalar", "xi"), attrs=(("operator", "mul"), ("name", "scaled"))),
            IRNode("binary", args=("scaled", "yi"), attrs=(("operator", "add"), ("name", "value"))),
            IRNode("store", args=("output", "i", "value")),
            IRNode("assign", attrs=(("target", "output"),)),
            IRNode("return", args=("output",)),
        ),
        invariants=("output length equals input length", "input buffers are read-only", "no out-of-bounds access"),
        metadata=(("dtype", "float64"), ("rank", 1)),
    )
    ir.validate()
    return ir


def derive_obligations(strategy: str, precision: str, layout: str, parallelism: str) -> tuple[str, ...]:
    obligations = [
        "behavioral-equivalence-to-canonical-spec",
        "bounds-safety",
        "deterministic-test-vectors",
        "ffi-cost-accounted",
    ]
    if "simd" in strategy:
        obligations.extend(("alignment-or-unaligned-load-safety", "vector-tail-correctness"))
    if "unrolled" in strategy:
        obligations.append("remainder-loop-correctness")
    if parallelism != "single":
        obligations.extend(("race-freedom", "partition-completeness", "determinism-policy-explicit"))
    if precision not in {"f64", "c128"}:
        obligations.append("reduced-precision-error-budget")
    if layout != "contiguous":
        obligations.append("layout-index-map-correctness")
    return tuple(dict.fromkeys(obligations))
