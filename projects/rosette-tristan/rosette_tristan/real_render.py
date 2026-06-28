from __future__ import annotations

import argparse
import json
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .latex_repair import render_diff_repair


@dataclass
class RealRenderResult:
    equation_id: str
    latex_candidate: str
    reference_latex: str | None
    candidate_png: str | None
    reference_png: str | None
    image_score: float
    symbol_score: float
    render_backend: str
    oak_status: str
    warnings: list[str] = field(default_factory=list)
    memory_minus: list[str] = field(default_factory=list)
    required_next_check: list[str] = field(default_factory=lambda: ["source_crop_compare", "human_or_oak_review"])

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _mathtext_expr(latex: str) -> str:
    text = latex.strip()
    if text.startswith("$") and text.endswith("$"):
        return text
    return f"${text}$"


def render_mathtext_png(latex: str, out_png: str | Path, dpi: int = 200) -> Path:
    """Render mathtext to PNG using matplotlib Agg.

    OAK note: this is real rendered mathtext, not a full system-LaTeX engine.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out = Path(out_png)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(6.0, 1.2), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.text(0.5, 0.5, _mathtext_expr(latex), ha="center", va="center", fontsize=26)
    fig.savefig(out, dpi=dpi, bbox_inches="tight", pad_inches=0.08, transparent=False)
    plt.close(fig)
    return out


def image_similarity(candidate_png: str | Path, reference_png: str | Path) -> float:
    import numpy as np
    import matplotlib.image as mpimg

    a = mpimg.imread(candidate_png).astype(float)
    b = mpimg.imread(reference_png).astype(float)
    if a.ndim == 2:
        a = np.stack([a, a, a], axis=-1)
    if b.ndim == 2:
        b = np.stack([b, b, b], axis=-1)
    channels = min(a.shape[-1], b.shape[-1], 3)
    a = a[..., :channels]
    b = b[..., :channels]
    height = max(a.shape[0], b.shape[0])
    width = max(a.shape[1], b.shape[1])
    aa = np.ones((height, width, channels), dtype=float)
    bb = np.ones((height, width, channels), dtype=float)
    aa[: a.shape[0], : a.shape[1], :] = a
    bb[: b.shape[0], : b.shape[1], :] = b
    mse = float(np.mean((aa - bb) ** 2))
    return round(max(0.0, 1.0 - min(1.0, mse * 8.0)), 4)


def real_render_diff(candidate: str, reference: str | None = None, out_dir: str | Path = "out_render", equation_id: str = "E1") -> RealRenderResult:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    symbolic = render_diff_repair(candidate, reference=reference, equation_id=equation_id)
    candidate_png = out / f"{equation_id}_candidate.png"
    reference_png = out / f"{equation_id}_reference.png" if reference is not None else None
    warnings: list[str] = ["mathtext backend: not full system LaTeX"]
    memory_minus: list[str] = list(symbolic.memory_minus)
    try:
        render_mathtext_png(symbolic.repaired_latex, candidate_png)
        ref_png_str: str | None = None
        image_score = 0.0
        if reference is not None and reference_png is not None:
            render_mathtext_png(reference, reference_png)
            ref_png_str = str(reference_png)
            image_score = image_similarity(candidate_png, reference_png)
            oak_status = "render_usable_not_certified" if image_score >= 0.9 and symbolic.symbol_score >= 0.85 else "render_review_needed"
            if image_score < 0.9:
                memory_minus.append("low_image_similarity_after_real_render")
        else:
            oak_status = "rendered_no_reference"
            warnings.append("No reference LaTeX or source crop provided; cannot compare render.")
        return RealRenderResult(
            equation_id=equation_id,
            latex_candidate=candidate,
            reference_latex=reference,
            candidate_png=str(candidate_png),
            reference_png=ref_png_str,
            image_score=image_score,
            symbol_score=symbolic.symbol_score,
            render_backend="matplotlib_mathtext",
            oak_status=oak_status,
            warnings=warnings,
            memory_minus=memory_minus,
        )
    except Exception as exc:
        return RealRenderResult(
            equation_id=equation_id,
            latex_candidate=candidate,
            reference_latex=reference,
            candidate_png=None,
            reference_png=None,
            image_score=0.0,
            symbol_score=symbolic.symbol_score,
            render_backend="matplotlib_mathtext",
            oak_status="render_failed",
            warnings=warnings + [str(exc)],
            memory_minus=memory_minus + ["real_render_failed"],
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rosette-real-render")
    parser.add_argument("candidate")
    parser.add_argument("--reference", default=None)
    parser.add_argument("--equation-id", default="E1")
    parser.add_argument("--out", default="out_real_render")
    args = parser.parse_args(argv)
    result = real_render_diff(args.candidate, reference=args.reference, out_dir=args.out, equation_id=args.equation_id)
    payload = result.to_dict()
    Path(args.out).mkdir(parents=True, exist_ok=True)
    (Path(args.out) / "real_render_report.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if result.oak_status != "render_failed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
