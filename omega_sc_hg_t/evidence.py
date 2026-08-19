from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LiteratureClaim:
    claim_id: str
    material: str
    claim: str
    value: float | None
    unit: str | None
    evidence_status: str
    source: str
    caveat: str


def borophene_2026_seed() -> tuple[LiteratureClaim, ...]:
    """Public evidence seed; intentionally does not invent missing EPC parameters."""
    source = "https://doi.org/10.1103/8l19-rdn2"
    return (
        LiteratureClaim(
            "borophene-aa-tc-2026",
            "AA-stacked bilayer borophene",
            "Predicted superconducting transition temperature at ambient pressure",
            68.0,
            "K",
            "THEORETICAL_PREDICTION",
            source,
            "Requires experimental replication; this value is not an experimental measurement.",
        ),
        LiteratureClaim(
            "borophene-aa-bond-2026",
            "AA-stacked bilayer borophene",
            "Direct covalent B-B interlayer bonding is identified as a superconductivity-enhancing motif",
            None,
            None,
            "MECHANISM_CLAIM",
            source,
            "Treat as a paper-supported mechanism claim, not a universal causal law.",
        ),
    )
