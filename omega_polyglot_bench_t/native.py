"""Native C, C++, and Rust build/FFI support using only the standard library."""

from __future__ import annotations

import ctypes
import shutil
import subprocess
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

SUPPORTED_NATIVE_BACKENDS = ("c", "cpp", "rust")


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_build_dir() -> Path:
    return repository_root() / ".omega_native"


def shared_library_suffix() -> str:
    if sys.platform.startswith("linux"):
        return ".so"
    if sys.platform == "darwin":
        return ".dylib"
    if sys.platform == "win32":
        return ".dll"
    raise RuntimeError(f"unsupported platform for native backends: {sys.platform}")


def native_library_path(backend: str, build_dir: Path | None = None) -> Path:
    if backend not in SUPPORTED_NATIVE_BACKENDS:
        raise ValueError(f"unsupported native backend: {backend}")
    root = build_dir or default_build_dir()
    return root / f"libomega_polyglot_{backend}{shared_library_suffix()}"


def _run(command: list[str], cwd: Path | None = None) -> None:
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        details = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"native build failed: {' '.join(command)}\n{details}")


def _compiler_flags() -> list[str]:
    if sys.platform.startswith("linux"):
        return ["-O3", "-shared", "-fPIC"]
    if sys.platform == "darwin":
        return ["-O3", "-dynamiclib", "-fPIC"]
    raise RuntimeError("automatic native compilation currently supports Linux and macOS")


def build_native(
    backends: Iterable[str] = SUPPORTED_NATIVE_BACKENDS,
    build_dir: Path | None = None,
) -> dict[str, Path]:
    """Compile requested native backends and return their shared-library paths."""

    requested = tuple(dict.fromkeys(backends))
    unknown = sorted(set(requested) - set(SUPPORTED_NATIVE_BACKENDS))
    if unknown:
        raise ValueError(f"unknown native backends: {', '.join(unknown)}")

    root = repository_root()
    output_root = build_dir or default_build_dir()
    output_root.mkdir(parents=True, exist_ok=True)
    built: dict[str, Path] = {}

    if "c" in requested:
        compiler = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
        if compiler is None:
            raise RuntimeError("C compiler not found (expected cc, gcc, or clang)")
        output = native_library_path("c", output_root)
        source = root / "native" / "omega_polyglot" / "c" / "omega_kernel.c"
        _run([compiler, *_compiler_flags(), str(source), "-o", str(output)])
        built["c"] = output

    if "cpp" in requested:
        compiler = shutil.which("c++") or shutil.which("g++") or shutil.which("clang++")
        if compiler is None:
            raise RuntimeError("C++ compiler not found (expected c++, g++, or clang++)")
        output = native_library_path("cpp", output_root)
        source = root / "native" / "omega_polyglot" / "cpp" / "omega_kernel.cpp"
        _run([compiler, *_compiler_flags(), "-std=c++17", str(source), "-o", str(output)])
        built["cpp"] = output

    if "rust" in requested:
        cargo = shutil.which("cargo")
        if cargo is None:
            raise RuntimeError("cargo not found")
        manifest = root / "native" / "omega_polyglot" / "rust" / "Cargo.toml"
        _run([cargo, "build", "--release", "--manifest-path", str(manifest)])
        rust_name = f"libomega_polyglot_rust{shared_library_suffix()}"
        source = manifest.parent / "target" / "release" / rust_name
        output = native_library_path("rust", output_root)
        if not source.exists():
            raise RuntimeError(f"Rust build succeeded but library was not found: {source}")
        shutil.copy2(source, output)
        built["rust"] = output

    return built


class NativeVectorAffine:
    """ctypes adapter for the shared C ABI implemented by every native backend."""

    def __init__(self, backend: str, build_dir: Path | None = None) -> None:
        self.backend = backend
        self.path = native_library_path(backend, build_dir)
        if not self.path.exists():
            raise FileNotFoundError(
                f"native backend '{backend}' is not built at {self.path}; run the build command first"
            )
        self._library = ctypes.CDLL(str(self.path))
        self._function = self._library.omega_vector_affine_f64
        pointer = ctypes.POINTER(ctypes.c_double)
        self._function.argtypes = [pointer, pointer, ctypes.c_double, pointer, ctypes.c_size_t]
        self._function.restype = ctypes.c_int

    def __call__(
        self,
        x: Sequence[float],
        y: Sequence[float],
        scalar: float,
    ) -> list[float]:
        if len(x) != len(y):
            raise ValueError("x and y must have the same length")
        length = len(x)
        array_type = ctypes.c_double * length
        x_array = array_type(*(float(value) for value in x))
        y_array = array_type(*(float(value) for value in y))
        output = array_type()
        status = self._function(x_array, y_array, float(scalar), output, length)
        if status != 0:
            raise RuntimeError(f"backend '{self.backend}' returned status {status}")
        return list(output)
