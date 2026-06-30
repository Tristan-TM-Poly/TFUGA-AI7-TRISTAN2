#!/usr/bin/env python3
"""Ω-HOSTING-T pre-buy green gate.

This script is a repository-level readiness check for the Hostinger KVM 8 plan.
It does not contact Hostinger, does not deploy, and does not require secrets.

Goal: make the repository green before the VPS is purchased.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_PATHS = [
    "docs/OMEGA_HOSTING_T.md",
    "infra/omega-hosting/README.md",
    "infra/omega-hosting/omega_hosting_manifest.yaml",
    "infra/omega-hosting/docker-compose.n8n.yml",
    "infra/omega-hosting/oak_deployment_checklist.md",
    "infra/omega-hosting/post_purchase_runbook.md",
    "infra/omega-hosting/bootstrap_ubuntu_24_04.sh",
    "tools/omega_hosting_t/oak_hosting_gate.py",
    "tools/omega_hosting_t/prebuy_green_gate.py",
]

FORBIDDEN_FILENAMES = {
    ".env",
    "id_rsa",
    "id_dsa",
    "id_ed25519",
    "secrets.json",
    "credentials.json",
}

SECRET_PATTERNS = [
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{40,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
    re.compile(r"BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY"),
]

TEXT_SUFFIXES = {
    ".md",
    ".py",
    ".yml",
    ".yaml",
    ".sh",
    ".txt",
    ".template",
    ".json",
}


@dataclass
class CheckResult:
    ok: bool
    name: str
    details: list[str] = field(default_factory=list)


@dataclass
class PrebuyReport:
    ok: bool
    results: list[CheckResult]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def check_required_paths() -> CheckResult:
    missing = [path for path in REQUIRED_PATHS if not (ROOT / path).exists()]
    return CheckResult(
        ok=not missing,
        name="required_paths",
        details=missing or ["All required pre-buy files exist."],
    )


def check_forbidden_filenames() -> CheckResult:
    hits: list[str] = []
    for path in ROOT.rglob("*"):
        if ".git" in path.parts:
            continue
        if path.is_file() and path.name in FORBIDDEN_FILENAMES:
            hits.append(str(path.relative_to(ROOT)))
    return CheckResult(
        ok=not hits,
        name="forbidden_filenames",
        details=hits or ["No forbidden local secret filenames are tracked in the tree."],
    )


def check_secret_patterns() -> CheckResult:
    hits: list[str] = []
    for path in ROOT.rglob("*"):
        if ".git" in path.parts or not path.is_file():
            continue
        if path.suffix not in TEXT_SUFFIXES and not path.name.endswith(".template"):
            continue
        text = read_text(path)
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                hits.append(f"{path.relative_to(ROOT)} matches {pattern.pattern}")
    return CheckResult(
        ok=not hits,
        name="secret_pattern_scan",
        details=hits or ["No high-confidence token/private-key pattern found in text files."],
    )


def check_compose_local_binding() -> CheckResult:
    compose_path = ROOT / "infra/omega-hosting/docker-compose.n8n.yml"
    if not compose_path.exists():
        return CheckResult(False, "compose_local_binding", ["docker-compose.n8n.yml is missing."])
    text = read_text(compose_path)
    expected = "127.0.0.1:${N8N_LOCAL_PORT:-5678}:5678"
    ok = expected in text
    return CheckResult(
        ok=ok,
        name="compose_local_binding",
        details=["n8n is bound to localhost for reverse-proxy exposure only." if ok else "n8n should bind to localhost, not public 0.0.0.0."],
    )


def check_oak_gate_blocks_ip_publication() -> CheckResult:
    from oak_hosting_gate import HostingInput, evaluate

    decision = evaluate(
        HostingInput(
            component_type="landing_page",
            asset_class="confidential_ip",
            public_exposure=True,
            reveals_unreviewed_ip=True,
        )
    )
    ok = not decision.allowed and decision.decision == "block_until_review"
    return CheckResult(
        ok=ok,
        name="oak_blocks_confidential_publication",
        details=[f"decision={decision.decision}; allowed={decision.allowed}; score={decision.score}/{decision.max_score}"],
    )


def run() -> PrebuyReport:
    results = [
        check_required_paths(),
        check_forbidden_filenames(),
        check_secret_patterns(),
        check_compose_local_binding(),
        check_oak_gate_blocks_ip_publication(),
    ]
    return PrebuyReport(ok=all(result.ok for result in results), results=results)


def main() -> int:
    report = run()
    print(json.dumps(asdict(report), indent=2, ensure_ascii=False))
    return 0 if report.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
