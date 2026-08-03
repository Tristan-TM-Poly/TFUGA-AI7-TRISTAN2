"""Persistent native buffers and zero-copy ctypes bindings."""

from __future__ import annotations

import ctypes
from array import array
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from ..native import native_library_path


def as_double_array(values: Iterable[float]) -> array:
    """Materialize values once as a native-endian contiguous float64 buffer."""

    return array("d", (float(value) for value in values))


def empty_double_array(length: int) -> array:
    """Allocate one reusable contiguous float64 output buffer."""

    if length < 0:
        raise ValueError("length must be non-negative")
    return array("d", [0.0]) * length


def _require_double_array(value: Any, *, name: str) -> array:
    if not isinstance(value, array) or value.typecode != "d":
        raise TypeError(
            f"{name} must be array('d') for a stable zero-copy native buffer"
        )
    return value


class NativeAffineLibrary:
    """Shared native function with zero-copy and prepared-call entry points."""

    def __init__(self, backend: str, build_dir: Path | None = None) -> None:
        self.backend = backend
        self.path = native_library_path(backend, build_dir)
        if not self.path.exists():
            raise FileNotFoundError(
                f"native backend '{backend}' is not built at {self.path}"
            )
        self._library = ctypes.CDLL(str(self.path))
        self._function = self._library.omega_vector_affine_f64
        pointer = ctypes.POINTER(ctypes.c_double)
        self._function.argtypes = [
            pointer,
            pointer,
            ctypes.c_double,
            pointer,
            ctypes.c_size_t,
        ]
        self._function.restype = ctypes.c_int

    def run_into(
        self,
        x: array,
        y: array,
        scalar: float,
        output: array,
    ) -> None:
        """Execute without copying payload data or allocating an output buffer."""

        x = _require_double_array(x, name="x")
        y = _require_double_array(y, name="y")
        output = _require_double_array(output, name="output")
        if not (len(x) == len(y) == len(output)):
            raise ValueError("x, y, and output must have the same length")

        length = len(x)
        if length == 0:
            null = ctypes.POINTER(ctypes.c_double)()
            status = self._function(null, null, float(scalar), null, 0)
        else:
            buffer_type = ctypes.c_double * length
            x_ref = buffer_type.from_buffer(x)
            y_ref = buffer_type.from_buffer(y)
            output_ref = buffer_type.from_buffer(output)
            status = self._function(
                x_ref,
                y_ref,
                float(scalar),
                output_ref,
                length,
            )
        if status != 0:
            raise RuntimeError(f"backend '{self.backend}' returned status {status}")

    def prepare(
        self,
        x: array,
        y: array,
        output: array | None = None,
    ) -> "PreparedAffineCall":
        """Pin reusable ctypes views outside the timed region."""

        return PreparedAffineCall(self, x, y, output)


class PreparedAffineCall:
    """Keep buffers and ctypes views alive across repeated native calls.

    The arrays must not be resized while this object exists because ctypes views
    hold direct addresses into their storage.
    """

    def __init__(
        self,
        library: NativeAffineLibrary,
        x: array,
        y: array,
        output: array | None = None,
    ) -> None:
        self.library = library
        self.x = _require_double_array(x, name="x")
        self.y = _require_double_array(y, name="y")
        if len(self.x) != len(self.y):
            raise ValueError("x and y must have the same length")

        self.output = output if output is not None else empty_double_array(len(self.x))
        self.output = _require_double_array(self.output, name="output")
        if len(self.output) != len(self.x):
            raise ValueError("output must have the same length as x and y")

        self.length = len(self.x)
        self._null = ctypes.POINTER(ctypes.c_double)()
        self._x_ref = None
        self._y_ref = None
        self._output_ref = None
        if self.length:
            buffer_type = ctypes.c_double * self.length
            self._x_ref = buffer_type.from_buffer(self.x)
            self._y_ref = buffer_type.from_buffer(self.y)
            self._output_ref = buffer_type.from_buffer(self.output)

    def run(self, scalar: float) -> array:
        """Execute FFI dispatch plus the native kernel into the persistent output."""

        if self.length:
            status = self.library._function(
                self._x_ref,
                self._y_ref,
                float(scalar),
                self._output_ref,
                self.length,
            )
        else:
            status = self.library._function(
                self._null,
                self._null,
                float(scalar),
                self._null,
                0,
            )
        if status != 0:
            raise RuntimeError(
                f"backend '{self.library.backend}' returned status {status}"
            )
        return self.output
