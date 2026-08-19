"""M⁻ Incident Codex for external actions.

The codex converts known failure modes into prevention rules. It is intentionally
plain Python data so it can be inspected, tested, and extended easily.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class IncidentRule:
    code: str
    incident: str
    prevention: str
    test_hint: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


DEFAULT_INCIDENT_RULES: tuple[IncidentRule, ...] = (
    IncidentRule(
        code="email_without_confirmation",
        incident="Final message action performed without explicit approval.",
        prevention="Downgrade to draft-only unless approved is true.",
        test_hint="send_email + approved false => allow_draft",
    ),
    IncidentRule(
        code="public_ip_disclosure",
        incident="Public output exposes invention details before IP review.",
        prevention="Require IP review for public actions touching IP.",
        test_hint="public true + touches_ip true + approved false => needs_approval",
    ),
    IncidentRule(
        code="destructive_no_rollback",
        incident="Important state changed without rollback or backup.",
        prevention="Block destructive action unless rollback is defined.",
        test_hint="destructive true + rollback none => block",
    ),
    IncidentRule(
        code="timezone_ambiguity",
        incident="Action scheduled in an ambiguous or wrong time context.",
        prevention="Require explicit timezone metadata for calendar-like actions.",
        test_hint="calendar scheduling without timezone => needs_approval",
    ),
    IncidentRule(
        code="secret_exposure",
        incident="Secret or credential is included in a public artifact.",
        prevention="Scan payloads before public release or commit.",
        test_hint="public artifact with secret-like metadata => block or review",
    ),
)


def incident_rules() -> list[dict[str, str]]:
    return [rule.to_dict() for rule in DEFAULT_INCIDENT_RULES]
