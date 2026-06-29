from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class LicenseClass(str, Enum):
    PERMISSIVE = "permissive"
    WEAK_COPYLEFT = "weak_copyleft"
    STRONG_COPYLEFT = "strong_copyleft"
    NETWORK_COPYLEFT = "network_copyleft"
    CONTENT_SHAREALIKE = "content_sharealike"
    UNKNOWN = "unknown"
    NO_LICENSE = "no_license"


@dataclass(frozen=True)
class LicenseDecision:
    license_id: str
    license_class: LicenseClass
    commercial_use_possible: bool
    direct_code_reuse: str
    attribution_required: bool
    sharealike_risk: str
    patent_note: str
    oak_status: str
    notes: tuple[str, ...]


PERMISSIVE = {"MIT", "BSD-2-Clause", "BSD-3-Clause", "ISC", "Zlib"}
APACHE = {"Apache-2.0"}
WEAK_COPYLEFT = {"LGPL-2.1", "LGPL-3.0", "MPL-2.0", "EPL-2.0"}
STRONG_COPYLEFT = {"GPL-2.0", "GPL-3.0"}
NETWORK_COPYLEFT = {"AGPL-3.0"}
CONTENT = {"CC-BY-SA-2.5", "CC-BY-SA-3.0", "CC-BY-SA-4.0"}
NO_LICENSE_MARKERS = {"NOASSERTION", "NONE", "NO-LICENSE", "UNLICENSED", "UNKNOWN", ""}


def normalize_license(license_id: str | None) -> str:
    if license_id is None:
        return "NOASSERTION"
    cleaned = license_id.strip()
    aliases = {
        "Apache License 2.0": "Apache-2.0",
        "MIT License": "MIT",
        "BSD 3-Clause": "BSD-3-Clause",
        "GPLv3": "GPL-3.0",
        "AGPLv3": "AGPL-3.0",
        "CC BY-SA 4.0": "CC-BY-SA-4.0",
    }
    return aliases.get(cleaned, cleaned)


def classify_license(license_id: str | None) -> LicenseDecision:
    lid = normalize_license(license_id)

    if lid in NO_LICENSE_MARKERS:
        return LicenseDecision(
            lid,
            LicenseClass.NO_LICENSE,
            commercial_use_possible=False,
            direct_code_reuse="blocked: no explicit license detected",
            attribution_required=True,
            sharealike_risk="unknown",
            patent_note="No patent grant can be assumed.",
            oak_status="OAK_RED_LICENSE",
            notes=("Read for ideas only; do not copy code into products.",),
        )

    if lid in APACHE:
        return LicenseDecision(
            lid,
            LicenseClass.PERMISSIVE,
            True,
            "allowed with license/notice preservation",
            True,
            "low",
            "explicit patent grant; preserve NOTICE",
            "OAK_GREEN_USE",
            ("Apache-2.0 includes an explicit patent license and NOTICE obligations when applicable.",),
        )

    if lid in PERMISSIVE:
        return LicenseDecision(
            lid,
            LicenseClass.PERMISSIVE,
            True,
            "allowed with attribution/license preservation",
            True,
            "low",
            "patent grant depends on license; MIT/BSD do not provide Apache-style explicit grant",
            "OAK_GREEN_USE",
            ("Keep copyright and license text.",),
        )

    if lid in WEAK_COPYLEFT:
        return LicenseDecision(
            lid,
            LicenseClass.WEAK_COPYLEFT,
            True,
            "conditional: respect file/library-level copyleft terms",
            True,
            "medium",
            "review license-specific patent clauses",
            "OAK_YELLOW_REVIEW",
            ("Prefer dependency use or clean adapters; review linking/distribution model.",),
        )

    if lid in STRONG_COPYLEFT:
        return LicenseDecision(
            lid,
            LicenseClass.STRONG_COPYLEFT,
            True,
            "conditional/high-risk for proprietary or mixed-license integration",
            True,
            "high",
            "review patent clauses and derivative-work implications",
            "OAK_YELLOW_OR_RED_REVIEW",
            ("Use in GPL-compatible projects, sandbox, or rewrite the invariant from scratch.",),
        )

    if lid in NETWORK_COPYLEFT:
        return LicenseDecision(
            lid,
            LicenseClass.NETWORK_COPYLEFT,
            True,
            "high-risk: network/service distribution obligations may apply",
            True,
            "very_high",
            "review patent clauses and network copyleft obligations",
            "OAK_RED_OR_STRICT_REVIEW",
            ("Do not integrate into SaaS/API without legal review.",),
        )

    if lid in CONTENT:
        return LicenseDecision(
            lid,
            LicenseClass.CONTENT_SHAREALIKE,
            True,
            "avoid direct code reuse unless attribution and share-alike compatibility are satisfied",
            True,
            "high",
            "content license, not a normal software license",
            "OAK_YELLOW_REWRITE_ONLY",
            ("Extract explanation/pattern; rewrite implementation and preserve attribution if quoting or adapting.",),
        )

    return LicenseDecision(
        lid,
        LicenseClass.UNKNOWN,
        False,
        "blocked pending manual/legal review",
        True,
        "unknown",
        "unknown",
        "OAK_RED_UNKNOWN_LICENSE",
        ("Unknown SPDX/license identifier.",),
    )


def batch_classify(licenses: Iterable[str | None]) -> list[LicenseDecision]:
    return [classify_license(item) for item in licenses]
