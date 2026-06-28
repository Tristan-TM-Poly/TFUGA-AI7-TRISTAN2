"""GitHub issue exporter for Ω-INFO²-T routes.

This module is intentionally non-mutating: it prepares issue titles, bodies,
and labels. A separate human-approved connector/action can create issues.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .models import InfoObject, Route


@dataclass(slots=True)
class GitHubIssueDraft:
    title: str
    body: str
    labels: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_ROUTE_LABELS: dict[Route, list[str]] = {
    Route.PROTOTYPE: ["omega-info2", "prototype", "oak-test"],
    Route.PATENT_HOLD: ["omega-info2", "ip-sensitive", "patent-hold"],
    Route.M_MINUS: ["omega-info2", "m-minus", "anti-error"],
    Route.OAK_REVIEW: ["omega-info2", "oak-review", "risk"],
    Route.CANON_CANDIDATE: ["omega-info2", "canon-candidate"],
    Route.COMPRESS: ["omega-info2", "cvcd"],
    Route.KEEP_RAW: ["omega-info2", "needs-revalidation"],
    Route.ARCHIVE: ["omega-info2", "archive"],
}


def issue_draft_from_info_object(obj: InfoObject) -> GitHubIssueDraft:
    """Prepare a GitHub issue draft from an InfoObject route."""
    route = obj.action.recommended_route
    title = f"[{route.value}] {obj.id}: {first_claim_or_concept(obj)}"
    labels = _ROUTE_LABELS.get(route, ["omega-info2"])
    body = render_issue_body(obj)
    return GitHubIssueDraft(title=title[:240], body=body, labels=labels)


def render_issue_body(obj: InfoObject) -> str:
    claims = "\n".join(f"- {claim.text}" for claim in obj.claims[:10]) or "- No claim extracted yet."
    residue = "\n".join(f"- {item}" for item in obj.oak.residue[:20]) or "- No residue recorded."
    checks_failed = "\n".join(f"- {item}" for item in obj.oak.checks_failed) or "- None"
    checks_passed = "\n".join(f"- {item}" for item in obj.oak.checks_passed) or "- None"
    concepts = ", ".join(obj.concepts[:20]) or "None"
    return f"""## Ω-INFO²-T Issue Draft

**Info ID:** `{obj.id}`  
**Route:** `{obj.action.recommended_route.value}`  
**Next action:** {obj.action.next_action or "Not specified"}  
**OAK status:** `{obj.oak.status.value}`

### Source

- Source: {obj.meta.source or "unknown"}
- Author: {obj.meta.author or "unknown"}
- License: {obj.meta.license}
- Domain: {obj.meta.domain}

### Scores

| Dimension | Score |
|---|---:|
| Truth | {obj.scores.truth:.3f} |
| Utility | {obj.scores.utility:.3f} |
| Fertility | {obj.scores.fertility:.3f} |
| Testability | {obj.scores.testability:.3f} |
| Risk | {obj.scores.risk:.3f} |
| IP sensitivity | {obj.scores.ip_sensitivity:.3f} |
| Source trust | {obj.scores.source_trust:.3f} |
| Compression gain | {obj.scores.compression_gain:.3f} |

### Claims

{claims}

### Concepts

{concepts}

### OAK checks passed

{checks_passed}

### OAK checks failed

{checks_failed}

### Residue / M⁻ candidates

{residue}

### OAK-safe note

This issue draft does not assert truth. It preserves source, uncertainty, route, residue, and next action for human/OAK review.
"""


def first_claim_or_concept(obj: InfoObject) -> str:
    if obj.claims:
        return obj.claims[0].text[:120]
    if obj.concepts:
        return obj.concepts[0][:120]
    return "unclassified information object"
