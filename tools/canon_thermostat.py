"""Canon Thermostat for Tristan CanonOS.

Classifies branch temperature from frozen to overheated and recommends safe
movement: wake, link, prototype, test, cool, or quarantine.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class CanonTemperature(IntEnum):
    T0_FROZEN = 0
    T1_COLD = 1
    T2_FERTILE = 2
    T3_HOT = 3
    T4_OVERHEATED = 4


@dataclass(frozen=True)
class CanonTemperatureReport:
    temperature: CanonTemperature
    label: str
    rationale: str
    recommended_action: str


def assess_canon_temperature(
    *,
    linked: bool = False,
    active: bool = False,
    testable: bool = False,
    high_novelty: bool = False,
    overclaim: bool = False,
    risk_debt_high: bool = False,
) -> CanonTemperatureReport:
    if overclaim or risk_debt_high:
        return CanonTemperatureReport(
            CanonTemperature.T4_OVERHEATED,
            "overheated",
            "Overclaim or high risk debt detected.",
            "Cool through OAK, RealityAnchor, tests, and quarantine if needed.",
        )

    if high_novelty and not testable:
        return CanonTemperatureReport(
            CanonTemperature.T3_HOT,
            "hot",
            "High novelty without enough testability.",
            "Add falsification tests and counterworlds before stronger claims.",
        )

    if active and testable:
        return CanonTemperatureReport(
            CanonTemperature.T2_FERTILE,
            "fertile",
            "Active, testable, and ready for prototype or benchmark.",
            "Prototype, test, and compile artifacts.",
        )

    if linked:
        return CanonTemperatureReport(
            CanonTemperature.T1_COLD,
            "cold",
            "Linked but not very active or fertile.",
            "Relate to current projects or archive if obsolete.",
        )

    return CanonTemperatureReport(
        CanonTemperature.T0_FROZEN,
        "frozen",
        "Unlinked or forgotten branch.",
        "Wake, link, or archive after audit.",
    )
