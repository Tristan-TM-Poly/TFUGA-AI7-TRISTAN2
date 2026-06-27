from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from typing import Iterable

from .adapters import extract_document
from .fidelity import write_fidelity_outputs
from .schemas import Claim, Equation, RosetteResult

EQUATION_PATTERNS = [
    re.compile(r"\$\$(.*?)\$\$", re.DOTALL),
    re.compile(r"\\\[(.*?)\\\]", re.DOTALL),
    re.compile(r"\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}", re.DOTALL),
]


def file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def extract_equations(blocks: Iterable) -> list[Equation]:
    equations: list[Equation] = []
    seen: set[tuple[str, str, int | None, int | None, int | None]] = set()
    for block in blocks:
        for pattern in EQUATION_PATTERNS:
            for match in pattern.finditer(block.text):
                latex = re.sub(r"\s+", " ", match.group(1).strip())
                key = (latex, block.source.path, block.source.page, block.source.span_start, block.source.span_end)
                if latex and key not in seen:
                    seen.add(key)
                    equations.append(Equation(latex=latex, source=block.source))
    return equations


def build_claims(blocks: Iterable) -> list[Claim]:
    triggers = ("we show", "we propose", "therefore", "we demonstrate", "we prove")
    claims: list[Claim] = []
    for block in blocks:
        if any(trigger in block.text.lower() for trigger in triggers):
            claims.append(Claim(claim=block.text[:500], source=block.source))
    return claims


def equations_to_tex(equations: list[Equation]) -> str:
    if not equations:
        return "% No equations detected.\n"
    return "\n\n".join(
        f"% equation_{idx} | page={eq.source.page} | extractor={eq.source.extractor}\n\\[\n{eq.latex}\n\\]"
        for idx, eq in enumerate(equations, 1)
    ) + "\n"


def run_fidelity_oak(result: RosetteResult, strict: bool = True) -> RosetteResult:
    if not result.blocks:
        result.oak_findings.append("HIGH: no text blocks extracted; try OCR/VLM route.")
        result.memory_minus.append("M⁻: empty extraction")
    if not result.extractor_runs:
        result.oak_findings.append("MEDIUM: no extractor run metadata preserved.")
        result.memory_minus.append("M⁻: missing extractor metadata")
    if not result.equations:
        result.oak_findings.append("LOW: no equations detected by heuristic parser.")
    for block in result.blocks:
        if block.source.span_start is None or block.source.span_end is None:
            result.oak_findings.append("MEDIUM: block lacks character span.")
            result.memory_minus.append("M⁻: block without source span")
            break
    for eq in result.equations:
        result.oak_findings.append("MEDIUM: equation requires render-diff-repair and dimensional OAK.")
        result.memory_minus.append(f"M⁻: uncertified equation `{eq.latex[:80]}`")
        if strict and eq.source.page is None:
            result.oak_findings.append("LOW: equation has no page reference in strict Fidelity mode.")
    for claim in result.claims:
        if not claim.evidence_ids:
            result.oak_findings.append("MEDIUM: claim candidate lacks explicit evidence links.")
    return result


class RosetteFidelityPipeline:
    def __init__(self, extractor: str = "auto", strict: bool = True) -> None:
        self.extractor = extractor
        self.strict = strict

    def process(self, input_path: str | Path) -> RosetteResult:
        path = Path(input_path)
        bundle = extract_document(path, extractor=self.extractor)
        result = RosetteResult(
            input_path=str(path),
            sha256=file_sha256(path),
            blocks=bundle.blocks,
            equations=extract_equations(bundle.blocks),
            claims=build_claims(bundle.blocks),
            oak_findings=[],
            memory_minus=[],
            extractor_runs=bundle.runs,
        )
        return run_fidelity_oak(result, strict=self.strict)

    def compile(self, input_path: str | Path, out_dir: str | Path) -> RosetteResult:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        result = self.process(input_path)
        (out / "document.md").write_text("\n\n".join(block.text for block in result.blocks), encoding="utf-8")
        (out / "document.json").write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        (out / "equations.tex").write_text(equations_to_tex(result.equations), encoding="utf-8")
        (out / "theory_graph.json").write_text(
            json.dumps(
                {
                    "claims": [asdict(claim) for claim in result.claims],
                    "equations": [asdict(eq) for eq in result.equations],
                    "tristan_links": ["Ω-ROSETTE-T", "OAK", "M⁻", "HGFM", "CVCD"],
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        write_fidelity_outputs(result, out)
        return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rosette-fidelity")
    parser.add_argument("input")
    parser.add_argument("--out", default="out")
    parser.add_argument("--extractor", choices=["auto", "text", "pymupdf"], default="auto")
    parser.add_argument("--relaxed", action="store_true", help="do not require page refs for strict equation OAK")
    args = parser.parse_args(argv)
    result = RosetteFidelityPipeline(extractor=args.extractor, strict=not args.relaxed).compile(args.input, args.out)
    print(f"blocks={len(result.blocks)} equations={len(result.equations)} claims={len(result.claims)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
