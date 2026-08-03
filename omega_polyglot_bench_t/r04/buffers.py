"""Zero-copy buffer protocol adapters for array('d'), memoryview and NumPy arrays."""
from __future__ import annotations

import ctypes
from array import array
from dataclasses import dataclass
from typing import Any, Iterable


def double_array(values: Iterable[float]) -> array:
    return array("d", (float(v) for v in values))


def zeros(length: int) -> array:
    if length < 0:
        raise ValueError("length must be non-negative")
    return array("d", [0.0]) * length


@dataclass
class BufferHandle:
    owner: Any
    view: memoryview
    length: int
    pointer: Any
    ctypes_view: Any | None
    readonly: bool


def _normalized_view(value: Any, *, writable: bool, name: str) -> memoryview:
    try:
        view = memoryview(value)
    except TypeError as exc:
        raise TypeError(f"{name} must expose the Python buffer protocol") from exc
    if view.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional")
    if not view.c_contiguous:
        raise ValueError(f"{name} must be C-contiguous")
    if view.itemsize != 8 or view.format not in {"d", "=d", "@d"}:
        raise TypeError(f"{name} must be native float64 (format 'd')")
    if writable and view.readonly:
        raise TypeError(f"{name} must be writable")
    return view


def bind_buffer(value: Any, *, writable: bool = False, name: str = "buffer") -> BufferHandle:
    """Bind a writable contiguous float64 buffer without copying.

    ctypes.from_buffer requires writable storage even for logically read-only native
    inputs, so zero-copy input buffers must currently be writable. This is recorded
    explicitly rather than silently copying read-only inputs.
    """
    view = _normalized_view(value, writable=writable, name=name)
    if view.readonly:
        raise TypeError(f"{name} is read-only; zero-copy ctypes binding requires writable storage")
    length = view.shape[0]
    if length == 0:
        pointer = ctypes.POINTER(ctypes.c_double)()
        return BufferHandle(value, view, 0, pointer, None, view.readonly)
    array_type = ctypes.c_double * length
    cview = array_type.from_buffer(view)
    pointer = ctypes.cast(cview, ctypes.POINTER(ctypes.c_double))
    return BufferHandle(value, view, length, pointer, cview, view.readonly)


def optional_numpy_zeros(length: int) -> Any | None:
    try:
        import numpy as np
    except ImportError:
        return None
    return np.zeros(length, dtype=np.float64)
