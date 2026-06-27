from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class RosetteBenchMetrics:
    text_fidelity: float = 0.0
    layout_fidelity: float = 0.0
    page_ref_coverage: float = 0.0
    bbox_coverage: float = 0.0
    equation_detection_f1: float = 0.0
    equation_render_score: float = 0.0
    table_structure_f1: float = 0.0
    claim_grounding_rate: float = 0.0
    code_execution_rate: float = 0.0
    oak_honesty_score: float = 1.0

    def to_dict(self) -> dict:
        return asdict(self)


def compute_oak_honesty(uncertain_count: int, risky_accepted_count: int) -> float:
    total = uncertain_count + risky_accepted_count
    if total == 0:
        return 1.0
    return max(0.0, uncertain_count / total)


def metrics_from_counts(blocks: int, page_refs: int, bboxes: int, claims: int, grounded_claims: int, uncertain: int, risky: int) -> RosetteBenchMetrics:
    denom_blocks = max(1, blocks)
    denom_claims = max(1, claims)
    return RosetteBenchMetrics(
        text_fidelity=1.0 if blocks else 0.0,
        layout_fidelity=page_refs / denom_blocks,
        page_ref_coverage=page_refs / denom_blocks,
        bbox_coverage=bboxes / denom_blocks,
        claim_grounding_rate=grounded_claims / denom_claims,
        oak_honesty_score=compute_oak_honesty(uncertain, risky),
    )
