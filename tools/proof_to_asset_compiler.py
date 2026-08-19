"""Proof-to-Asset Compiler for Ω-AIT-RESEARCH-FACTORY-T.

Transforms a result into a reviewed asset plan. It does not publish, sell,
merge, or contact anyone.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProofAssetPlan:
    result: str
    technical_note: str
    demo: str
    benchmark: str
    review_packet: str
    product_hypothesis: str
    value_experiment: str
    safe_next_action: str


def compile_proof_to_asset(result: str, *, slug: str | None = None, ready_for_public_review: bool = False) -> ProofAssetPlan:
    safe_slug = slug or "".join(ch.lower() if ch.isalnum() else "_" for ch in result).strip("_")[:60] or "result"
    next_action = "prepare reviewed release packet" if ready_for_public_review else "keep internal and strengthen evidence"
    return ProofAssetPlan(
        result=result,
        technical_note=f"docs/technical_notes/{safe_slug}.md",
        demo=f"examples/{safe_slug}_demo.md",
        benchmark=f"benchmarks/{safe_slug}_benchmark.md",
        review_packet=f"docs/review_packets/{safe_slug}_review.md",
        product_hypothesis=f"docs/value_hypotheses/{safe_slug}.md",
        value_experiment=f"docs/value_experiments/{safe_slug}.md",
        safe_next_action=next_action,
    )
