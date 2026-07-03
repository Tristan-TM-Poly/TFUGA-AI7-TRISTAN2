from __future__ import annotations

from dataclasses import asdict, dataclass


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


@dataclass(frozen=True)
class DigestScore:
    fit: float = 0.5
    license_compatibility: float = 0.5
    tests: float = 0.5
    security: float = 0.5
    maintainability: float = 0.5
    cvcd_compressibility: float = 0.5
    utility: float = 0.5
    community_activity: float = 0.5
    risk: float = 0.2

    def normalized(self) -> "DigestScore":
        return DigestScore(**{k: clamp01(v) for k, v in asdict(self).items()})

    def value(self) -> float:
        s = self.normalized()
        return round(
            0.20 * s.fit
            + 0.15 * s.license_compatibility
            + 0.15 * s.tests
            + 0.15 * s.security
            + 0.10 * s.maintainability
            + 0.10 * s.cvcd_compressibility
            + 0.10 * s.utility
            + 0.05 * s.community_activity
            - 0.20 * s.risk,
            4,
        )


def score_source(**kwargs: float) -> float:
    return DigestScore(**kwargs).value()


def score_band(score: float) -> str:
    if score >= 0.85:
        return "OAK_GREEN_CANON"
    if score >= 0.70:
        return "OAK_GREEN_USE"
    if score >= 0.50:
        return "OAK_YELLOW_SANDBOX"
    if score >= 0.30:
        return "OAK_RED_REWRITE_ONLY"
    return "M_MINUS_ARCHIVE"
