"""Action routing for Ω-INFO²-T."""

from __future__ import annotations

from .models import InfoAction, InfoObject, OAKStatus, Route


def route_information(obj: InfoObject) -> Route:
    """Route an information object to its next safest useful action."""
    s = obj.scores
    status = obj.oak.status

    if status == OAKStatus.FALSIFIED or s.truth < 0.25:
        route = Route.M_MINUS
        next_action = "Preserve as negative memory and create anti-error rule."
    elif s.risk > 0.85 or status == OAKStatus.DANGEROUS:
        route = Route.OAK_REVIEW
        next_action = "Human/OAK risk review before any publication or automation."
    elif s.ip_sensitivity > 0.70 or status == OAKStatus.IP_SENSITIVE:
        route = Route.PATENT_HOLD
        next_action = "Hold publication; prepare IP classification and prior-art scan."
    elif s.testability > 0.70 and s.fertility > 0.70:
        route = Route.PROTOTYPE
        next_action = "Create benchmark or prototype against baseline."
    elif s.utility > 0.80 and s.truth > 0.60 and s.source_trust > 0.50:
        route = Route.CANON_CANDIDATE
        next_action = "Link into canon after counter-evidence search."
    elif s.compression_gain > 0.70 and s.fertility > 0.50:
        route = Route.COMPRESS
        next_action = "Extract CVCD invariants and preserve residue."
    elif s.freshness < 0.25:
        route = Route.KEEP_RAW
        next_action = "Revalidate freshness before using."
    else:
        route = Route.ARCHIVE
        next_action = "Archive with metadata; do not overclaim."

    obj.action = InfoAction(recommended_route=route, next_action=next_action)
    return route
