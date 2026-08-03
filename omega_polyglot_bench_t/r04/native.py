"""Typed R0.4 ABI loader and reusable prepared kernels."""
from __future__ import annotations

import ctypes
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .buffers import BufferHandle, bind_buffer, zeros
from .build import library_path

AFFINE_VARIANTS = ("scalar", "unrolled4", "avx2", "parallel")
CHAIN_VARIANTS = ("scalar", "avx2", "parallel")
REDUCTION_VARIANTS = ("scalar", "avx2", "parallel")


class KernelLibrary:
    def __init__(self, backend: str, profile: str, build_dir: Path | None = None) -> None:
        self.backend = backend
        self.profile = profile
        self.path = library_path(backend, profile, build_dir)
        if not self.path.exists():
            raise FileNotFoundError(self.path)
        self.lib = ctypes.CDLL(str(self.path))
        p = ctypes.POINTER(ctypes.c_double)
        self.affine: dict[str, Any] = {}
        for variant in AFFINE_VARIANTS:
            fn = getattr(self.lib, f"omega_affine_{variant}_f64")
            fn.argtypes = [p, p, ctypes.c_double, p, ctypes.c_size_t]
            fn.restype = ctypes.c_int
            self.affine[variant] = fn
        self.inplace = self.lib.omega_affine_inplace_f64
        self.inplace.argtypes = [p, p, ctypes.c_double, ctypes.c_size_t]
        self.inplace.restype = ctypes.c_int
        self.chains: dict[str, Any] = {}
        for variant, symbol in (("scalar", "omega_affine_chain_f64"), ("avx2", "omega_affine_chain_avx2_f64"), ("parallel", "omega_affine_chain_parallel_f64")):
            fn = getattr(self.lib, symbol)
            fn.argtypes = [p, p, p, ctypes.c_double, ctypes.c_double, p, ctypes.c_size_t]
            fn.restype = ctypes.c_int
            self.chains[variant] = fn
        self.triad = self.lib.omega_triad_f64
        self.triad.argtypes = [p, p, p, ctypes.c_double, p, ctypes.c_size_t]
        self.triad.restype = ctypes.c_int
        self.reductions: dict[tuple[str, str], Any] = {}
        for operation in ("sum", "dot"):
            for variant, suffix in (("scalar", "f64"), ("avx2", "avx2_f64"), ("parallel", "parallel_f64")):
                fn = getattr(self.lib, f"omega_{operation}_{suffix}")
                fn.argtypes = [p, ctypes.c_size_t] if operation == "sum" else [p, p, ctypes.c_size_t]
                fn.restype = ctypes.c_double
                self.reductions[(operation, variant)] = fn
        self.feature_mask_fn = self.lib.omega_feature_mask
        self.feature_mask_fn.argtypes = []
        self.feature_mask_fn.restype = ctypes.c_uint64

    @property
    def feature_mask(self) -> int:
        return int(self.feature_mask_fn())

    @property
    def features(self) -> tuple[str, ...]:
        mask = self.feature_mask
        return tuple(name for bit, name in ((1, "avx2"), (2, "fma"), (4, "openmp")) if mask & bit)

    def prepare_affine(self, variant: str, x: Any, y: Any, output: Any | None = None) -> "PreparedAffine":
        if variant not in self.affine:
            raise ValueError(f"unknown affine variant: {variant}")
        output = zeros(len(x)) if output is None else output
        return PreparedAffine(self, variant, bind_buffer(x, name="x"), bind_buffer(y, name="y"), bind_buffer(output, writable=True, name="output"))

    def prepare_inplace(self, x: Any, y: Any) -> "PreparedInplace":
        return PreparedInplace(self, bind_buffer(x, writable=True, name="x"), bind_buffer(y, name="y"))

    def prepare_chain(self, x: Any, y: Any, z: Any, output: Any | None = None, *, variant: str = "scalar") -> "PreparedChain":
        if variant not in self.chains:
            raise ValueError(f"unknown chain variant: {variant}")
        output = zeros(len(x)) if output is None else output
        return PreparedChain(self, variant, bind_buffer(x, name="x"), bind_buffer(y, name="y"), bind_buffer(z, name="z"), bind_buffer(output, writable=True, name="output"))

    def prepare_reduction(self, operation: str, x: Any, y: Any | None = None, *, variant: str = "scalar") -> "PreparedReduction":
        if operation not in {"sum", "dot"}:
            raise ValueError(operation)
        if variant not in REDUCTION_VARIANTS:
            raise ValueError(variant)
        return PreparedReduction(self, operation, variant, bind_buffer(x, name="x"), bind_buffer(y, name="y") if y is not None else None)


@dataclass
class PreparedAffine:
    library: KernelLibrary
    variant: str
    x: BufferHandle
    y: BufferHandle
    output: BufferHandle

    def __post_init__(self) -> None:
        if not (self.x.length == self.y.length == self.output.length):
            raise ValueError("x, y and output lengths differ")

    def run(self, scalar: float) -> Any:
        status = self.library.affine[self.variant](self.x.pointer, self.y.pointer, float(scalar), self.output.pointer, self.x.length)
        if status:
            raise RuntimeError(f"native affine failed with status {status}")
        return self.output.owner


@dataclass
class PreparedInplace:
    library: KernelLibrary
    x: BufferHandle
    y: BufferHandle

    def __post_init__(self) -> None:
        if self.x.length != self.y.length:
            raise ValueError("x and y lengths differ")

    def run(self, scalar: float) -> Any:
        status = self.library.inplace(self.x.pointer, self.y.pointer, float(scalar), self.x.length)
        if status:
            raise RuntimeError(f"native inplace affine failed with status {status}")
        return self.x.owner


@dataclass
class PreparedChain:
    library: KernelLibrary
    variant: str
    x: BufferHandle
    y: BufferHandle
    z: BufferHandle
    output: BufferHandle

    def __post_init__(self) -> None:
        if len({self.x.length, self.y.length, self.z.length, self.output.length}) != 1:
            raise ValueError("chain buffer lengths differ")

    def run(self, a: float, b: float) -> Any:
        status = self.library.chains[self.variant](self.x.pointer, self.y.pointer, self.z.pointer, float(a), float(b), self.output.pointer, self.x.length)
        if status:
            raise RuntimeError(f"native chain failed with status {status}")
        return self.output.owner


@dataclass
class PreparedReduction:
    library: KernelLibrary
    operation: str
    variant: str
    x: BufferHandle
    y: BufferHandle | None = None

    def __post_init__(self) -> None:
        if self.operation == "dot":
            if self.y is None or self.x.length != self.y.length:
                raise ValueError("dot requires equal-length x and y")

    def run(self) -> float:
        fn = self.library.reductions[(self.operation, self.variant)]
        if self.operation == "sum":
            return float(fn(self.x.pointer, self.x.length))
        assert self.y is not None
        return float(fn(self.x.pointer, self.y.pointer, self.x.length))
