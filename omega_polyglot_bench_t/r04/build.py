"""Build the R0.4 native kernel matrix with conservative and host-tuned profiles."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

BACKENDS = ("c", "cpp", "rust")
PROFILES = ("portable", "native", "openmp")


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_build_dir() -> Path:
    return repository_root() / ".omega_native_r04"


def suffix() -> str:
    if sys.platform.startswith("linux"):
        return ".so"
    if sys.platform == "darwin":
        return ".dylib"
    if sys.platform == "win32":
        return ".dll"
    raise RuntimeError(f"unsupported platform: {sys.platform}")


def library_path(backend: str, profile: str, build_dir: Path | None = None) -> Path:
    if backend not in BACKENDS:
        raise ValueError(f"unknown backend: {backend}")
    if profile not in PROFILES:
        raise ValueError(f"unknown profile: {profile}")
    return (build_dir or default_build_dir()) / f"libomega_r04_{backend}_{profile}{suffix()}"


def _run(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    completed = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False)
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"build failed: {' '.join(command)}\n{detail}")


def _shared_flags() -> list[str]:
    if sys.platform.startswith("linux"):
        return ["-O3", "-shared", "-fPIC"]
    if sys.platform == "darwin":
        return ["-O3", "-dynamiclib", "-fPIC"]
    raise RuntimeError("automatic R0.4 compilation supports Linux and macOS")


def _profile_flags(profile: str) -> list[str]:
    if profile == "portable":
        return []
    if profile == "native":
        return ["-march=native", "-mtune=native"]
    if profile == "openmp":
        return ["-march=native", "-mtune=native", "-fopenmp"]
    raise ValueError(profile)


def build_native(
    *,
    backends: tuple[str, ...] = BACKENDS,
    profiles: tuple[str, ...] = PROFILES,
    build_dir: Path | None = None,
    tolerate_unavailable: bool = True,
) -> dict[str, dict[str, str]]:
    """Build all requested combinations and return a status matrix."""
    root = repository_root()
    out = build_dir or default_build_dir()
    out.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict[str, str]] = {}

    for backend in backends:
        results[backend] = {}
        for profile in profiles:
            try:
                target = library_path(backend, profile, out)
                if backend == "c":
                    compiler = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
                    if compiler is None:
                        raise RuntimeError("C compiler not found")
                    source = root / "native/omega_polyglot/r04/c/omega_kernels.c"
                    _run([compiler, *_shared_flags(), *_profile_flags(profile), str(source), "-o", str(target)])
                elif backend == "cpp":
                    compiler = shutil.which("c++") or shutil.which("g++") or shutil.which("clang++")
                    if compiler is None:
                        raise RuntimeError("C++ compiler not found")
                    source = root / "native/omega_polyglot/r04/cpp/omega_kernels.cpp"
                    _run([compiler, *_shared_flags(), *_profile_flags(profile), "-std=c++17", str(source), "-o", str(target)])
                elif backend == "rust":
                    cargo = shutil.which("cargo")
                    if cargo is None:
                        raise RuntimeError("cargo not found")
                    manifest = root / "native/omega_polyglot/r04/rust/Cargo.toml"
                    target_dir = out / f"cargo-{profile}"
                    env = os.environ.copy()
                    rustflags = [] if profile == "portable" else ["-C", "target-cpu=native"]
                    if profile == "openmp":
                        rustflags = ["-C", "target-cpu=native"]
                    env["RUSTFLAGS"] = " ".join(rustflags)
                    env["CARGO_TARGET_DIR"] = str(target_dir)
                    _run([cargo, "build", "--release", "--manifest-path", str(manifest)], env=env)
                    built = target_dir / "release" / f"libomega_polyglot_r04_rust{suffix()}"
                    if not built.exists():
                        raise RuntimeError(f"Rust library not found: {built}")
                    shutil.copy2(built, target)
                results[backend][profile] = str(target)
            except Exception as exc:
                if not tolerate_unavailable:
                    raise
                results[backend][profile] = f"UNAVAILABLE: {exc}"
    return results
