from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class IPGuardianReport:
    copyright_status: str = "unknown"
    license: str = "unknown"
    allowed_outputs: list[str] = field(default_factory=lambda: [
        "short_summary",
        "private_notes",
        "citation",
        "derived_code_if_cleanroom",
    ])
    forbidden_outputs: list[str] = field(default_factory=lambda: [
        "long_verbatim_copy",
        "public_republication",
    ])
    patent_relevance: dict[str, str] = field(default_factory=lambda: {
        "level": "unknown",
        "reason": "source method may inspire an extension",
    })
    tristan_extension_status: dict[str, str] = field(default_factory=lambda: {
        "source_method": "existing_or_unknown",
        "extension": "speculative_new",
        "publishability": "needs_review",
    })
    oak_rules: list[str] = field(default_factory=lambda: [
        "reading is not ownership",
        "understanding is not republication",
        "extension is not copying",
        "implementation must respect license and patent risk",
    ])

    def to_dict(self) -> dict:
        return asdict(self)


def classify_ip_guardian(text: str = "", license_hint: str | None = None) -> IPGuardianReport:
    report = IPGuardianReport()
    if license_hint:
        report.license = license_hint
    low = text.lower()
    if "patent" in low or "claim" in low:
        report.patent_relevance = {"level": "medium", "reason": "document contains patent/claim-like language"}
    if "confidential" in low or "proprietary" in low:
        report.copyright_status = "restricted_or_confidential"
        report.allowed_outputs = ["private_notes", "short_summary"]
        report.forbidden_outputs.append("external_sharing")
    return report
