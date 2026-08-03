"""Dated, conservative seed for the Tristan Grand Atlas portfolio."""
from __future__ import annotations

from .core import ClaimBoundary, Evidence, NextAction, Prototype, Relation, Snapshot, DIMENSIONS, SIGNALS

HEADS = {
    "Tristan-TM-Poly/TFUGA-AI7-TRISTAN2": "8f1fca34025929889779930ebec46c68c8c11d22",
    "Tristan-TM-Poly/TTM-TFUGA-AI7-TRISTAN2": "fb49a34d39fffbca3d3eb5d3f5ec1cf99384b049",
    "Tristan-TM-Poly/Tristan_Tardif-Morency_TFUG": "9171a06a7dbf3db1ad152008ce5d8d4896398e9d",
    "Tristan-TM-Poly/PEFA-FractalEnergySystem": "d5ee7dbf7d7eb75790f63ee3a40671f60d8c3f80",
    "Tristan-TM-Poly/TFACC": "399bf8e3c6671d00da31c60033b06aa004da9817",
    "Tristan-TM-Poly/Tristan_Tardif-Morency_TFUGAG": "c28e51d7d39b43544b46a56fac0abb3047200744",
}


def dims(**updates: int) -> dict[str, int]:
    base = {name: 0 for name in DIMENSIONS}
    base.update({"truth": 2, "documentation": 3, "github": 3, "risk_control": 3, "novelty": 3, "utility": 3, "falsifiability": 2})
    base.update(updates)
    return base


def sigs(**updates: bool) -> dict[str, bool]:
    base = {name: False for name in SIGNALS}
    base.update(updates)
    return base


def ev(kind: str, ref: str, strength: str = "OBSERVED", note: str = "") -> Evidence:
    return Evidence(kind, ref, strength, note)


def action(title: str, kind: str, hours: int, evidence: str, external: bool = False) -> NextAction:
    return NextAction(title, kind, hours, evidence, external)


def p(prototype_id: str, name: str, category: str, repository: str, ref: str, summary: str, *, dimensions: dict[str, int], signals: dict[str, bool], evidence: tuple[Evidence, ...], status: str, claim: str, risks: tuple[str, ...], next_action: NextAction, relations: tuple[Relation, ...] = (), independent: bool = False, certified: bool = False, limitations: tuple[str, ...] = (), tags: tuple[str, ...] = ()) -> Prototype:
    return Prototype(prototype_id, name, category, repository, ref, summary, dimensions, signals, evidence, ClaimBoundary(status, claim, certified, independent, limitations), risks, next_action, relations, tags)


def seed_snapshot() -> Snapshot:
    from .seed_main_a import items as items_a
    from .seed_main_b import items as items_b
    from .seed_external_a import items as items_c
    from .seed_external_b import items as items_d
    from .seed_grand_atlas import items as items_e

    main = "Tristan-TM-Poly/TFUGA-AI7-TRISTAN2"
    ttm = "Tristan-TM-Poly/TTM-TFUGA-AI7-TRISTAN2"
    tfug = "Tristan-TM-Poly/Tristan_Tardif-Morency_TFUG"
    prototypes = (
        items_a(main, ttm, tfug)
        + items_b(main, ttm, tfug)
        + items_c(main, ttm, tfug)
        + items_d(main, ttm, tfug)
        + items_e(main, ttm, tfug)
    )
    return Snapshot(
        "prototype-portfolio-2026-08-03-r02-grand-atlas",
        "2026-08-03T20:54:00Z",
        HEADS,
        prototypes,
        policy_version="r0.2",
    )
