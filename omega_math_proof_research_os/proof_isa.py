from __future__ import annotations

from enum import StrEnum


class ProofOp(StrEnum):
    ASSUME = "ASSUME"
    INTRO = "INTRO"
    SPECIALIZE = "SPECIALIZE"
    GENERALIZE = "GENERALIZE"
    NEGATE = "NEGATE"
    SPLIT = "SPLIT"
    CASE = "CASE"
    CONSTRUCT = "CONSTRUCT"
    WITNESS = "WITNESS"
    REWRITE = "REWRITE"
    SUBSTITUTE = "SUBSTITUTE"
    APPLY = "APPLY"
    INDUCT = "INDUCT"
    COUNTEREXAMPLE = "COUNTEREXAMPLE"
    CONTRADICT = "CONTRADICT"
    CLOSE = "CLOSE"


class DiscoveryOp(StrEnum):
    SPECIALIZE = "SPECIALIZE"
    GENERALIZE = "GENERALIZE"
    ANALOGIZE = "ANALOGIZE"
    COMPUTE_CASES = "COMPUTE_CASES"
    SEARCH_COUNTEREXAMPLE = "SEARCH_COUNTEREXAMPLE"
    RELAX = "RELAX"
    STRENGTHEN = "STRENGTHEN"
    CHANGE_REPRESENTATION = "CHANGE_REPRESENTATION"
    INVENT_LEMMA = "INVENT_LEMMA"


def normalize_ops(ops: list[str]) -> tuple[str, ...]:
    """Normalize a tactic trace into a stable uppercase genome component."""

    return tuple(op.strip().upper().replace("-", "_") for op in ops if op.strip())
