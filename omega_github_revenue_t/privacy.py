from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .ledger import SensitiveDataError, reject_sensitive_fields


@dataclass(frozen=True)
class PrivacyFinding:
    category: str
    path: str
    severity: str
    fingerprint: str


_SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
    ("openai_like_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("stripe_secret", re.compile(r"\b(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{16,}\b")),
)

_VALUE_FIELD_HINTS = {
    "bank account",
    "account number",
    "routing number",
    "transit number",
    "institution number",
    "void cheque",
    "social insurance number",
    "home address",
}


def _fingerprint(value: str) -> str:
    import hashlib

    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:16]


def scan_text(text: str, *, path: str = "$") -> list[PrivacyFinding]:
    findings: list[PrivacyFinding] = []
    lowered = text.lower()
    for hint in sorted(_VALUE_FIELD_HINTS):
        if hint in lowered:
            findings.append(
                PrivacyFinding(
                    category="sensitive_context_hint",
                    path=path,
                    severity="review",
                    fingerprint=_fingerprint(hint),
                )
            )
    for category, pattern in _SECRET_PATTERNS:
        for match in pattern.finditer(text):
            findings.append(
                PrivacyFinding(
                    category=category,
                    path=path,
                    severity="critical",
                    fingerprint=_fingerprint(match.group(0)),
                )
            )
    return findings


def scan_payload(payload: Any, *, path: str = "$") -> list[PrivacyFinding]:
    reject_sensitive_fields(payload)
    findings: list[PrivacyFinding] = []
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            findings.extend(scan_payload(value, path=f"{path}.{key}"))
    elif isinstance(payload, (list, tuple)):
        for index, value in enumerate(payload):
            findings.extend(scan_payload(value, path=f"{path}[{index}]"))
    elif isinstance(payload, str):
        findings.extend(scan_text(payload, path=path))
    return findings


def reject_secret_values(payload: Any) -> None:
    findings = [item for item in scan_payload(payload) if item.severity == "critical"]
    if findings:
        categories = ", ".join(sorted({item.category for item in findings}))
        raise SensitiveDataError(f"secret-like value rejected: {categories}")


def redact_text(text: str, *, replacement: str = "[REDACTED]") -> tuple[str, list[PrivacyFinding]]:
    findings = scan_text(text)
    redacted = text
    for _, pattern in _SECRET_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted, findings


def summarize_findings(findings: Iterable[PrivacyFinding]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for finding in findings:
        summary[finding.category] = summary.get(finding.category, 0) + 1
    return dict(sorted(summary.items()))
