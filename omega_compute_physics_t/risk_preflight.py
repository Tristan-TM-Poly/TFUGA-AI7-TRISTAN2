"""Conservative static risk preflight for benchmark planning in R0.6.

The scanner intentionally over-approximates risk. It looks for imports/calls that
may imply network access, credentials, subprocesses, writes or privileged/external
side effects. Absence of a flag is not a security guarantee.
"""
from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from .benchmark_contract import BenchmarkRisk


_NETWORK_NAMES = {"socket", "requests", "urllib", "http", "httpx", "aiohttp", "ftplib", "smtplib"}
_CREDENTIAL_NAMES = {"keyring", "boto3", "google.auth", "azure.identity", "secret", "token", "password"}
_SUBPROCESS_NAMES = {"subprocess", "os.system", "system", "popen", "run", "check_call", "check_output"}
_PRIVILEGED_NAMES = {"sudo", "setuid", "chmod", "chown", "mount", "umount"}
_EXTERNAL_NAMES = {"send", "post", "put", "delete", "publish", "upload", "commit", "push"}
_WRITE_CALLS = {"write_text", "write_bytes", "unlink", "remove", "rmdir", "rename", "replace", "mkdir"}


@dataclass(frozen=True)
class RiskFinding:
    category: str
    symbol: str
    line: int
    reason: str


@dataclass(frozen=True)
class RiskPreflightReport:
    module: str
    findings: tuple[RiskFinding, ...]
    risk: BenchmarkRisk
    confidence: str = "static-overapproximation"
    status: str = "benchmark-risk-preflight"
    oak_warning: str = (
        "Static risk scanning can produce both false positives and false negatives. "
        "A clean report is not a sandbox or security certification."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "findings": [asdict(row) for row in self.findings],
            "risk": asdict(self.risk),
        }


def _name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return ""


def scan_source_risk(source: str, *, module: str = "<memory>") -> RiskPreflightReport:
    tree = ast.parse(source, filename=module)
    findings: list[RiskFinding] = []

    def add(category: str, symbol: str, node: ast.AST, reason: str) -> None:
        findings.append(RiskFinding(category, symbol, int(getattr(node, "lineno", 0)), reason))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top in _NETWORK_NAMES:
                    add("network", alias.name, node, "network-capable module imported")
                if alias.name in _CREDENTIAL_NAMES or top in {name.split(".")[0] for name in _CREDENTIAL_NAMES}:
                    add("credentials", alias.name, node, "credential/secret-capable module imported")
                if top == "subprocess":
                    add("external_side_effects", alias.name, node, "subprocess-capable module imported")
        elif isinstance(node, ast.ImportFrom) and node.module:
            top = node.module.split(".")[0]
            if top in _NETWORK_NAMES:
                add("network", node.module, node, "network-capable module imported")
            if top in {name.split(".")[0] for name in _CREDENTIAL_NAMES}:
                add("credentials", node.module, node, "credential/secret-capable module imported")
            if top == "subprocess":
                add("external_side_effects", node.module, node, "subprocess-capable module imported")
        elif isinstance(node, ast.Call):
            symbol = _name(node.func).lower()
            leaf = symbol.split(".")[-1]
            if any(part in _NETWORK_NAMES for part in symbol.split(".")) or leaf in {"urlopen", "request"}:
                add("network", symbol, node, "call may perform network access")
            if leaf in _WRITE_CALLS:
                add("destructive_io", symbol, node, "filesystem-mutating call")
            if leaf == "open":
                mode = None
                if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                    mode = str(node.args[1].value)
                for kw in node.keywords:
                    if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                        mode = str(kw.value.value)
                if mode and any(flag in mode for flag in ("w", "a", "+", "x")):
                    add("destructive_io", symbol, node, f"file open mode {mode!r} can mutate data")
            if leaf in {name.split(".")[-1] for name in _SUBPROCESS_NAMES} and (
                "subprocess" in symbol or leaf in {"system", "popen", "check_call", "check_output"}
            ):
                add("external_side_effects", symbol, node, "process execution or shell interaction")
            if leaf in _PRIVILEGED_NAMES:
                add("privileged_operations", symbol, node, "privileged/system-mutating operation")
            if leaf in _EXTERNAL_NAMES and any(part in symbol for part in ("client", "api", "repo", "mail", "request")):
                add("external_side_effects", symbol, node, "possible external mutation or publication")
        elif isinstance(node, ast.Name):
            lowered = node.id.lower()
            if any(marker in lowered for marker in ("password", "secret", "api_key", "token")):
                add("credentials", node.id, node, "credential-like symbol referenced")

    categories = {row.category for row in findings}
    risk = BenchmarkRisk(
        network="network" in categories,
        credentials="credentials" in categories,
        destructive_io="destructive_io" in categories,
        external_side_effects="external_side_effects" in categories,
        privileged_operations="privileged_operations" in categories,
    )
    unique = {(f.category, f.symbol, f.line, f.reason): f for f in findings}
    ordered = tuple(sorted(unique.values(), key=lambda f: (f.line, f.category, f.symbol)))
    return RiskPreflightReport(module=module, findings=ordered, risk=risk)
