from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
import re
from difflib import SequenceMatcher


COMMON_SYMBOL_CONFUSIONS: dict[str, str] = {
    " p ": " \\rho ",
    " varepsilon ": " \\epsilon ",
    "\\varepsilon": "\\epsilon",
    "\\nu": "v",
    " partial ": " \\partial ",
    " d/dt ": " \\frac{d}{dt} ",
}


@dataclass
class RenderRepairResult:
    equation_id: str
    latex_candidate: str
    repaired_latex: str
    reference_latex: str | None = None
    render_score: float = 0.0
    symbol_score: float = 0.0
    layout_score: float = 0.0
    oak_status: str = "uncertain"
    repair_history: list[str] = field(default_factory=list)
    memory_minus: list[str] = field(default_factory=list)
    required_next_check: list[str] = field(default_factory=lambda: ["real_latex_render", "source_crop_compare"])

    def to_dict(self) -> dict:
        return asdict(self)


def normalize_latex(text: str) -> str:
    text = text.strip()
    text = text.replace("\\left", "").replace("\\right", "")
    text = re.sub(r"\s+", "", text)
    return text


def similarity(a: str, b: str) -> float:
    if not a and not b:
        return 1.0
    return SequenceMatcher(None, normalize_latex(a), normalize_latex(b)).ratio()


def apply_symbol_repairs(candidate: str) -> tuple[str, list[str], list[str]]:
    padded = f" {candidate} "
    history: list[str] = []
    memory_minus: list[str] = []
    for wrong, right in COMMON_SYMBOL_CONFUSIONS.items():
        if wrong in padded:
            padded = padded.replace(wrong, right)
            history.append(f"repaired `{wrong.strip()}` -> `{right.strip()}`")
            memory_minus.append(f"symbol_confusion: {wrong.strip()}/{right.strip()}")
    repaired = padded.strip()
    if "_" in repaired and "{" not in repaired:
        memory_minus.append("missing_subscript_braces_possible")
    return repaired, history, memory_minus


def render_diff_repair(candidate: str, reference: str | None = None, equation_id: str = "E1") -> RenderRepairResult:
    repaired, history, memory_minus = apply_symbol_repairs(candidate)
    if reference is None:
        symbol_score = 0.5 if repaired else 0.0
        render_score = 0.0
        layout_score = 0.0
        oak_status = "needs_reference_render"
    else:
        symbol_score = similarity(repaired, reference)
        render_score = symbol_score
        layout_score = min(1.0, 0.8 + 0.2 * symbol_score)
        oak_status = "usable_not_certified" if symbol_score >= 0.85 else "repair_needed"
        if symbol_score < 0.85:
            memory_minus.append("low_symbol_similarity_after_repair")
    return RenderRepairResult(
        equation_id=equation_id,
        latex_candidate=candidate,
        repaired_latex=repaired,
        reference_latex=reference,
        render_score=round(render_score, 4),
        symbol_score=round(symbol_score, 4),
        layout_score=round(layout_score, 4),
        oak_status=oak_status,
        repair_history=history,
        memory_minus=memory_minus,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rosette-render")
    parser.add_argument("candidate")
    parser.add_argument("--reference", default=None)
    parser.add_argument("--equation-id", default="E1")
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    result = render_diff_repair(args.candidate, reference=args.reference, equation_id=args.equation_id)
    payload = result.to_dict()
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
