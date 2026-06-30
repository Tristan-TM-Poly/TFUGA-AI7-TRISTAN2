#!/usr/bin/env python3
"""Ω-HOSTING-T VPS readiness doctor.

Safe local/server checker. It reads public system facts and prints a readiness
report for an Ubuntu VPS. It does not deploy anything and does not read private
runtime values.
"""

from __future__ import annotations

import json
import platform
import shutil
import socket
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class Probe:
    name: str
    ok: bool
    details: str


@dataclass
class DoctorReport:
    ok: bool
    probes: list[Probe] = field(default_factory=list)


def run_cmd(args: list[str]) -> tuple[int, str]:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=8, check=False)
        return result.returncode, (result.stdout + result.stderr).strip()
    except Exception as exc:  # pragma: no cover - operational guard
        return 999, repr(exc)


def probe_os() -> Probe:
    pretty = platform.platform()
    os_release = Path("/etc/os-release")
    text = os_release.read_text(errors="replace") if os_release.exists() else ""
    ok = "Ubuntu" in text and "24.04" in text
    return Probe("ubuntu_24_04", ok, pretty)


def probe_ram() -> Probe:
    meminfo = Path("/proc/meminfo")
    if not meminfo.exists():
        return Probe("ram", False, "meminfo unavailable")
    values = {}
    for line in meminfo.read_text().splitlines():
        if ":" in line:
            key, rest = line.split(":", 1)
            values[key] = rest.strip()
    total_kb = int(values.get("MemTotal", "0 kB").split()[0])
    total_gb = total_kb / 1024 / 1024
    return Probe("ram_min_24gb", total_gb >= 24, f"{total_gb:.1f} GiB detected")


def probe_disk() -> Probe:
    usage = shutil.disk_usage("/")
    total_gb = usage.total / 1024**3
    free_gb = usage.free / 1024**3
    ok = total_gb >= 150 and free_gb >= 50
    return Probe("disk_capacity", ok, f"total={total_gb:.1f} GiB free={free_gb:.1f} GiB")


def probe_commands() -> list[Probe]:
    required = ["docker", "git", "curl", "ufw"]
    probes: list[Probe] = []
    for command in required:
        path = shutil.which(command)
        probes.append(Probe(f"command_{command}", path is not None, path or "missing"))
    return probes


def probe_ports() -> list[Probe]:
    probes = []
    for port in [80, 443]:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        try:
            result = sock.connect_ex(("127.0.0.1", port))
            probes.append(Probe(f"port_{port}_local", True, "checked" if result in {0, 111} else f"connect_ex={result}"))
        finally:
            sock.close()
    return probes


def probe_docker() -> Probe:
    code, out = run_cmd(["docker", "--version"])
    return Probe("docker_version", code == 0, out or "docker unavailable")


def run() -> DoctorReport:
    probes = [probe_os(), probe_ram(), probe_disk(), probe_docker()]
    probes.extend(probe_commands())
    probes.extend(probe_ports())
    return DoctorReport(ok=all(p.ok for p in probes), probes=probes)


def main() -> int:
    report = run()
    print(json.dumps(asdict(report), indent=2, ensure_ascii=False))
    return 0 if report.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
