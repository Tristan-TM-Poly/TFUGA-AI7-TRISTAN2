"""Portable MachineGenome metadata and bounded micro-calibration for R0.5.

The calibration numbers are empirical fingerprints of the current process and
host state. They are not vendor peak specs and are not portable guarantees.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import os
import platform
import statistics
import time
from typing import Any


@dataclass(frozen=True)
class MachineGenome:
    system: str
    release: str
    machine: str
    processor: str
    python: str
    logical_cpus: int | None
    page_size: int | None
    physical_memory_bytes: int | None
    load_average_1m: float | None
    scalar_ops_per_s: float | None = None
    bytes_copy_per_s: float | None = None
    calibration_repeats: int = 0
    status: str = "empirical-machine-genome"
    oak_warning: str = (
        "MachineGenome calibration is host/process/state dependent. It is not a vendor "
        "specification, security boundary or cross-hardware performance guarantee."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _physical_memory() -> int | None:
    try:
        pages = int(os.sysconf("SC_PHYS_PAGES"))
        page = int(os.sysconf("SC_PAGE_SIZE"))
        return pages * page
    except (AttributeError, OSError, ValueError):
        return None


def fingerprint_machine() -> MachineGenome:
    try:
        page_size = int(os.sysconf("SC_PAGE_SIZE"))
    except (AttributeError, OSError, ValueError):
        page_size = None
    try:
        load = float(os.getloadavg()[0])
    except (AttributeError, OSError):
        load = None
    return MachineGenome(
        system=platform.system(),
        release=platform.release(),
        machine=platform.machine(),
        processor=platform.processor(),
        python=platform.python_version(),
        logical_cpus=os.cpu_count(),
        page_size=page_size,
        physical_memory_bytes=_physical_memory(),
        load_average_1m=load,
    )


def calibrate_machine(*, repeats: int = 3, scalar_iterations: int = 200_000, copy_bytes: int = 2_000_000) -> MachineGenome:
    if repeats < 1 or repeats > 20:
        raise ValueError("repeats must be in [1, 20]")
    if scalar_iterations < 1 or scalar_iterations > 20_000_000:
        raise ValueError("scalar_iterations outside bounded calibration range")
    if copy_bytes < 1 or copy_bytes > 100_000_000:
        raise ValueError("copy_bytes outside bounded calibration range")

    scalar_rates: list[float] = []
    copy_rates: list[float] = []
    source = bytearray(copy_bytes)
    for _ in range(repeats):
        x = 1.000001
        start = time.perf_counter()
        for i in range(scalar_iterations):
            x = x * 1.0000001 + (i & 7) * 1e-9
        elapsed = max(time.perf_counter() - start, 1e-12)
        scalar_rates.append(scalar_iterations / elapsed)

        start = time.perf_counter()
        _ = source[:]
        elapsed = max(time.perf_counter() - start, 1e-12)
        copy_rates.append(copy_bytes / elapsed)
        if x == -1.0:  # keep computation observably live
            raise AssertionError("unreachable")

    base = fingerprint_machine()
    return MachineGenome(
        **{k: v for k, v in asdict(base).items() if k not in {"scalar_ops_per_s", "bytes_copy_per_s", "calibration_repeats", "status", "oak_warning"}},
        scalar_ops_per_s=statistics.median(scalar_rates),
        bytes_copy_per_s=statistics.median(copy_rates),
        calibration_repeats=repeats,
    )
