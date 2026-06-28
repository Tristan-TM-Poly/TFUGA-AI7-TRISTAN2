from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .real_render import image_similarity, render_mathtext_png


@dataclass
class SourceCropCompareResult:
    equation_id: str
    latex_candidate: str
    candidate_png: str | None
    source_crop_png: str | None
    image_score: float
    oak_status: str
    render_backend: str = "matplotlib_mathtext"
    crop_backend: str = "png_or_pymupdf"
    warnings: list[str] = field(default_factory=list)
    memory_minus: list[str] = field(default_factory=list)
    required_next_check: list[str] = field(default_factory=lambda: ["bbox_validation", "human_or_oak_review"])

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_bbox(text: str) -> tuple[float, float, float, float]:
    parts = [float(part.strip()) for part in text.split(",")]
    if len(parts) != 4:
        raise ValueError("bbox must have four comma-separated numbers: x0,y0,x1,y1")
    x0, y0, x1, y1 = parts
    if x1 <= x0 or y1 <= y0:
        raise ValueError("bbox must satisfy x1 > x0 and y1 > y0")
    return x0, y0, x1, y1


def extract_pdf_crop_to_png(pdf_path: str | Path, page: int, bbox: tuple[float, float, float, float], out_png: str | Path, zoom: float = 2.0) -> Path:
    """Extract a PDF crop to PNG using PyMuPDF.

    Coordinates use PDF page space. Page is 1-based for CLI/user-facing safety.
    """
    try:
        import fitz  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("PDF crop support requires `pip install -e .[pdf]` or PyMuPDF") from exc

    pdf = Path(pdf_path)
    if page < 1:
        raise ValueError("page must be 1-based and >= 1")
    doc = fitz.open(pdf)
    if page > len(doc):
        raise ValueError(f"page {page} is outside document with {len(doc)} pages")
    x0, y0, x1, y1 = bbox
    clip = fitz.Rect(x0, y0, x1, y1)
    mat = fitz.Matrix(zoom, zoom)
    pix = doc[page - 1].get_pixmap(matrix=mat, clip=clip, alpha=False)
    out = Path(out_png)
    out.parent.mkdir(parents=True, exist_ok=True)
    pix.save(out)
    return out


def compare_candidate_to_source_crop(candidate_latex: str, source_crop_png: str | Path, out_dir: str | Path = "out_source_crop", equation_id: str = "E1") -> SourceCropCompareResult:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    candidate_png = out / f"{equation_id}_candidate.png"
    source_crop = Path(source_crop_png)
    warnings = ["mathtext render compared to source crop; not full certification"]
    memory_minus: list[str] = []
    try:
        render_mathtext_png(candidate_latex, candidate_png)
        score = image_similarity(candidate_png, source_crop)
        if score >= 0.92:
            status = "source_crop_match_not_certified"
        elif score >= 0.75:
            status = "source_crop_review_needed"
            memory_minus.append("medium_source_crop_similarity")
        else:
            status = "source_crop_mismatch"
            memory_minus.append("low_source_crop_similarity")
        return SourceCropCompareResult(
            equation_id=equation_id,
            latex_candidate=candidate_latex,
            candidate_png=str(candidate_png),
            source_crop_png=str(source_crop),
            image_score=score,
            oak_status=status,
            warnings=warnings,
            memory_minus=memory_minus,
        )
    except Exception as exc:
        return SourceCropCompareResult(
            equation_id=equation_id,
            latex_candidate=candidate_latex,
            candidate_png=None,
            source_crop_png=str(source_crop),
            image_score=0.0,
            oak_status="source_crop_compare_failed",
            warnings=warnings + [str(exc)],
            memory_minus=["source_crop_compare_failed"],
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rosette-source-crop")
    parser.add_argument("candidate")
    parser.add_argument("--source-crop", default=None, help="Existing source crop PNG to compare against")
    parser.add_argument("--pdf", default=None, help="PDF to crop when --source-crop is not provided")
    parser.add_argument("--page", type=int, default=1, help="1-based PDF page")
    parser.add_argument("--bbox", default=None, help="PDF bbox x0,y0,x1,y1")
    parser.add_argument("--equation-id", default="E1")
    parser.add_argument("--out", default="out_source_crop")
    args = parser.parse_args(argv)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    source_crop = args.source_crop
    if source_crop is None:
        if not args.pdf or not args.bbox:
            parser.error("provide either --source-crop PNG or both --pdf and --bbox")
        bbox = parse_bbox(args.bbox)
        source_crop = str(extract_pdf_crop_to_png(args.pdf, args.page, bbox, out / f"{args.equation_id}_source_crop.png"))

    result = compare_candidate_to_source_crop(args.candidate, source_crop, out_dir=out, equation_id=args.equation_id)
    payload = result.to_dict()
    (out / "source_crop_compare_report.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if result.oak_status != "source_crop_compare_failed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
