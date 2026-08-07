from __future__ import annotations

from .analysis import cvcd_signature
from .models import OAKReport, Program


def oak_report(program: Program, *, native_verified: bool = False) -> OAKReport:
    metrics = cvcd_signature(program)
    claims = [
        "ASM-IR is structurally valid and analyzable",
        "reported static metrics are deterministic for this IR",
    ]
    limitations = [
        "static cost estimates are not runtime benchmarks",
        "performance is microarchitecture- and workload-dependent",
        "AArch64 backend is not natively executed by the default x86-64 CI runner",
        "floating-point reassociation is outside the R1 integer kernel scope",
    ]
    if native_verified:
        claims.append("the built-in x86-64 dot_u64 fixture matched its C reference in native CI")
    else:
        limitations.append("native equivalence has not been asserted for this report")
    return OAKReport(
        valid=True,
        authority="review_only",
        human_review_required=True,
        automatic_merge_allowed=False,
        claims=tuple(claims),
        limitations=tuple(limitations),
        metrics=metrics,
    )
