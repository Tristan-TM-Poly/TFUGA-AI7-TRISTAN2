from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import hashlib
import os
import platform
import re
import shutil
import subprocess
from typing import Iterable


_ARCH_ALIASES = {
    "amd64": "x86_64",
    "x64": "x86_64",
    "x86-64": "x86_64",
    "arm64": "aarch64",
}


def normalize_architecture(value: str | None = None) -> str:
    raw = (value or platform.machine() or "unknown").strip().lower().replace(" ", "_")
    return _ARCH_ALIASES.get(raw, raw)


def _read_text(path: str | Path) -> str | None:
    try:
        value = Path(path).read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None
    return value or None


def _read_int(path: str | Path) -> int | None:
    text = _read_text(path)
    if text is None:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def parse_size_bytes(value: str | None) -> int | None:
    """Parse Linux cache-size forms such as 48K, 2M or raw bytes."""

    if value is None:
        return None
    match = re.fullmatch(r"\s*(\d+)\s*([KMGTP]?)(?:i?[Bb])?\s*", value, flags=re.I)
    if not match:
        return None
    amount = int(match.group(1))
    suffix = match.group(2).upper()
    scale = {"": 1, "K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4, "P": 1024**5}
    return amount * scale[suffix]


def _cpuinfo_blocks() -> list[dict[str, str]]:
    text = _read_text("/proc/cpuinfo")
    if text is None:
        return []
    blocks: list[dict[str, str]] = []
    for raw_block in re.split(r"\n\s*\n", text):
        block: dict[str, str] = {}
        for line in raw_block.splitlines():
            key, separator, value = line.partition(":")
            if separator:
                block[key.strip().lower()] = value.strip()
        if block:
            blocks.append(block)
    return blocks


def _feature_set(block: dict[str, str]) -> tuple[str, ...]:
    raw = block.get("flags") or block.get("features") or ""
    return tuple(sorted({item for item in raw.split() if item}))


def _topology_from_cpuinfo(blocks: list[dict[str, str]]) -> tuple[int | None, int | None]:
    core_pairs: set[tuple[str, str]] = set()
    sockets: set[str] = set()
    for block in blocks:
        physical = block.get("physical id")
        core = block.get("core id")
        if physical is not None:
            sockets.add(physical)
        if physical is not None and core is not None:
            core_pairs.add((physical, core))
    return (len(core_pairs) or None, len(sockets) or None)


@dataclass(frozen=True)
class CacheDescriptor:
    index: str
    level: int | None
    cache_type: str | None
    size_bytes: int | None
    line_size_bytes: int | None
    ways_of_associativity: int | None
    number_of_sets: int | None
    shared_cpu_list: str | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def cache_descriptors() -> tuple[CacheDescriptor, ...]:
    root = Path("/sys/devices/system/cpu/cpu0/cache")
    if not root.is_dir():
        return ()
    rows: list[CacheDescriptor] = []
    try:
        indexes = sorted(root.glob("index*"), key=lambda path: path.name)
    except OSError:
        return ()
    for index in indexes:
        rows.append(
            CacheDescriptor(
                index=index.name,
                level=_read_int(index / "level"),
                cache_type=_read_text(index / "type"),
                size_bytes=parse_size_bytes(_read_text(index / "size")),
                line_size_bytes=_read_int(index / "coherency_line_size"),
                ways_of_associativity=_read_int(index / "ways_of_associativity"),
                number_of_sets=_read_int(index / "number_of_sets"),
                shared_cpu_list=_read_text(index / "shared_cpu_list"),
            )
        )
    return tuple(rows)


def _frequency_context() -> dict[str, object]:
    root = Path("/sys/devices/system/cpu/cpu0/cpufreq")
    return {
        "scaling_governor": _read_text(root / "scaling_governor"),
        "scaling_driver": _read_text(root / "scaling_driver"),
        "current_khz": _read_int(root / "scaling_cur_freq"),
        "min_khz": _read_int(root / "scaling_min_freq"),
        "max_khz": _read_int(root / "scaling_max_freq"),
        "cpuinfo_min_khz": _read_int(root / "cpuinfo_min_freq"),
        "cpuinfo_max_khz": _read_int(root / "cpuinfo_max_freq"),
    }


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tool_version(path: str) -> str | None:
    env = os.environ.copy()
    env["LC_ALL"] = "C"
    try:
        completed = subprocess.run(
            [path, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
            timeout=3,
            env=env,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    first = completed.stdout.splitlines()[0].strip() if completed.stdout else ""
    return first or None


def toolchain_manifest(names: Iterable[str] = ("cc", "gcc", "clang", "as", "ld", "rustc")) -> dict[str, object]:
    result: dict[str, object] = {}
    for name in names:
        path = shutil.which(name)
        result[name] = {
            "available": path is not None,
            "path": path,
            "version": _tool_version(path) if path else None,
        }
    return result


def microarchitecture_manifest(*, include_toolchains: bool = False) -> dict[str, object]:
    """Collect provenance for P5/P6 evidence without making a performance claim.

    All fields are observational and best-effort. Missing kernel/sysfs information
    remains ``None`` rather than being guessed.
    """

    blocks = _cpuinfo_blocks()
    first = blocks[0] if blocks else {}
    features = _feature_set(first)
    physical_cores, socket_count = _topology_from_cpuinfo(blocks)
    vendor = first.get("vendor_id") or first.get("cpu implementer") or first.get("hardware")
    model_name = first.get("model name") or first.get("processor") or platform.processor() or None

    result: dict[str, object] = {
        "schema_version": 1,
        "architecture": normalize_architecture(),
        "vendor": vendor,
        "family": first.get("cpu family") or first.get("cpu architecture"),
        "model": first.get("model") or first.get("cpu part"),
        "stepping": first.get("stepping") or first.get("revision"),
        "model_name": model_name,
        "logical_cpus": os.cpu_count(),
        "physical_cores_observed": physical_cores,
        "socket_count_observed": socket_count,
        "isa_features": list(features),
        "hypervisor_flag_present": "hypervisor" in features,
        "caches": [row.to_dict() for row in cache_descriptors()],
        "frequency_context": _frequency_context(),
        "operating_system": platform.system() or "unknown",
        "os_release": platform.release() or "unknown",
        "kernel_or_platform": platform.platform(),
        "github_actions": os.environ.get("GITHUB_ACTIONS") == "true",
        "runner": {
            "name": os.environ.get("RUNNER_NAME"),
            "os": os.environ.get("RUNNER_OS"),
            "arch": os.environ.get("RUNNER_ARCH"),
            "image_os": os.environ.get("ImageOS"),
        },
        "claim_scope": "observational_hardware_context_only",
        "sources": {
            "proc_cpuinfo": bool(blocks),
            "sysfs_cache": bool(cache_descriptors()),
            "sysfs_cpufreq": Path("/sys/devices/system/cpu/cpu0/cpufreq").is_dir(),
        },
    }
    if include_toolchains:
        result["toolchains"] = toolchain_manifest()
    return result
