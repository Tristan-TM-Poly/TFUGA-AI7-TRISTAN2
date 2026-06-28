from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .real_render import real_render_diff
from .source_crop_compare import compare_candidate_to_source_crop, extract_pdf_crop_to_png, parse_bbox


@dataclass
class VisualOAKReport:
    equation_id: str
    latex_candidate: str
    real_render: dict[str, Any]
    source_crop_compare: dict[str, Any] | None
    visual_oak_score: float
    oak_status: str
    warnings: list[str] = field(default_factory=list)
    memory_minus: list[str] = field(default_factory=list)
    required_next_check: list[str] = field(default_factory=lambda: [
        "bbox_validation",
        "symbolic_equivalence",
        "source_context_check",
        "human_or_oak_review",
    ])

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def combine_scores(real_render_score: float, source_crop_score: float | None) -> float:
    if source_crop_score is None:
        return round(0.55 * real_render_score, 4)
    return round((0.35 * real_render_score) + (0.65 * source_crop_score), 4)


def classify_visual_oak(score: float, has_source_crop: bool) -> str:
    if not has_source_crop:
        return "visual_rendered_no_source_crop"
    if score >= 0.92:
        return "visual_match_not_certified"
    if score >= 0.75:
        return "visual_review_needed"
    return "visual_mismatch"


def run_visual_oak(
    candidate_latex: str,
    reference_latex: str | None = None,
    source_crop_png: str | Path | None = None,
    pdf_path: str | Path | None = None,
    page: int = 1,
    bbox: tuple[float, float, float, float] | None = None,
    out_dir: str | Path = "out_visual_oak",
    equation_id: str = "E1",
) -> VisualOAKReport:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    warnings = ["Visual OAK improves evidence; it is not proof of mathematical equivalence."]
    memory_minus: list[str] = []

    real = real_render_diff(candidate_latex, reference=reference_latex, out_dir=out / "real_render", equation_id=equation_id)
    memory_minus.extend(real.memory_minus)

    crop_result = None
    crop_path: str | Path | None = source_crop_png
    if crop_path is None and pdf_path is not None and bbox is not None:
        crop_path = extract_pdf_crop_to_png(pdf_path, page, bbox, out / f"{equation_id}_source_crop.png")
    if crop_path is not None:
        crop_result_obj = compare_candidate_to_source_crop(candidate_latex, crop_path, out_dir=out / "source_crop", equation_id=equation_id)
        crop_result = crop_result_obj.to_dict()
        memory_minus.extend(crop_result_obj.memory_minus)
    else:
        warnings.append("No source crop provided; Visual OAK cannot compare against the original document region.")
        memory_minus.append("visual_oak_missing_source_crop")

    source_score = crop_result["image_score"] if crop_result is not None else None
    score = combine_scores(real.image_score, source_score)
    status = classify_visual_oak(score, has_source_crop=crop_result is not None)

    return VisualOAKReport(
        equation_id=equation_id,
        latex_candidate=candidate_latex,
        real_render=real.to_dict(),
        source_crop_compare=crop_result,
        visual_oak_score=score,
        oak_status=status,
        warnings=warnings,
        memory_minus=memory_minus,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rosette-visual-oak")
    parser.add_argument("candidate")
    parser.add_argument("--reference", default=None)
    parser.add_argument("--source-crop", default=None)
    parser.add_argument("--pdf", default=None)
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--bbox", default=None, help="PDF bbox x0,y0,x1,y1")
    parser.add_argument("--equation-id", default="E1")
    parser.add_argument("--out", default="out_visual_oak")
    args = parser.parse_args(argv)

    bbox = parse_bbox(args.bbox) if args.bbox else None
    report = run_visual_oak(
        args.candidate,
        reference_latex=args.reference,
        source_crop_png=args.source_crop,
        pdf_path=args.pdf,
        page=args.page,
        bbox=bbox,
        out_dir=args.out,
        equation_id=args.equation_id,
    )
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    payload = report.to_dict()
    (out / "visual_oak_report.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if report.oak_status != "visual_mismatch" else 1


if __name__ == "__main__":
    raise SystemExit(main())
