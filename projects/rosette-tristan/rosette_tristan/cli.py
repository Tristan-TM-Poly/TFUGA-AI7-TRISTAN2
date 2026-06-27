from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any


@dataclass
class SourceRef:
    path: str
    page: int | None = None
    span_start: int | None = None
    span_end: int | None = None
    method: str = "text"


@dataclass
class Block:
    kind: str
    text: str
    source: SourceRef
    confidence: float = 0.9
    oak_status: str = "usable"


@dataclass
class Equation:
    latex: str
    source: SourceRef
    confidence: float = 0.82
    oak_status: str = "usable"
    notes: list[str] = field(default_factory=list)


@dataclass
class Claim:
    claim: str
    source: SourceRef | None = None
    evidence_ids: list[str] = field(default_factory=list)
    confidence: float = 0.55
    oak_status: str = "uncertain"


@dataclass
class RosetteResult:
    input_path: str
    sha256: str
    blocks: list[Block]
    equations: list[Equation]
    claims: list[Claim]
    oak_findings: list[str]
    memory_minus: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


EQUATION_PATTERNS = [
    re.compile(r"\$\$(.*?)\$\$", re.DOTALL),
    re.compile(r"\\\[(.*?)\\\]", re.DOTALL),
    re.compile(r"\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}", re.DOTALL),
]


def ingest(path: str | Path) -> tuple[Path, str]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    return p, sha256(p.read_bytes()).hexdigest()


def extract_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        try:
            import fitz  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("PDF support requires `pip install -e .[pdf]`") from exc
        doc = fitz.open(path)
        return "\n\n".join(page.get_text("text") for page in doc)
    return path.read_text(encoding="utf-8", errors="replace")


def split_blocks(text: str, path: Path) -> list[Block]:
    blocks: list[Block] = []
    cursor = 0
    for para in [p.strip() for p in text.split("\n\n") if p.strip()]:
        start = text.find(para, cursor)
        end = start + len(para)
        cursor = end
        kind = "heading" if para.startswith("#") else "paragraph"
        blocks.append(Block(kind=kind, text=para, source=SourceRef(str(path), span_start=start, span_end=end)))
    return blocks


def extract_equations(blocks: list[Block]) -> list[Equation]:
    equations: list[Equation] = []
    seen: set[tuple[str, str, int | None, int | None]] = set()
    for block in blocks:
        for pattern in EQUATION_PATTERNS:
            for match in pattern.finditer(block.text):
                latex = re.sub(r"\s+", " ", match.group(1).strip())
                key = (latex, block.source.path, block.source.span_start, block.source.span_end)
                if latex and key not in seen:
                    seen.add(key)
                    equations.append(Equation(latex=latex, source=block.source))
    return equations


def build_claims(blocks: list[Block]) -> list[Claim]:
    triggers = ("we show", "we propose", "therefore", "we demonstrate", "we prove")
    claims = []
    for block in blocks:
        low = block.text.lower()
        if any(t in low for t in triggers):
            claims.append(Claim(claim=block.text[:500], source=block.source))
    return claims


def equations_to_tex(equations: list[Equation]) -> str:
    if not equations:
        return "% No equations detected.\n"
    return "\n\n".join(f"% equation_{i}\n\\[\n{eq.latex}\n\\]" for i, eq in enumerate(equations, 1)) + "\n"


def code_from_equations(equations: list[Equation]) -> str:
    lines = [
        '"""Generated Rosette equation skeleton. OAK: symbolic extraction is not validation."""',
        "from __future__ import annotations",
        "",
    ]
    for i, eq in enumerate(equations, 1):
        safe = eq.latex.replace('"""', "'''")
        lines += [
            f"def equation_{i}(*args, **kwargs):",
            f"    r'''Source LaTeX: {safe}'''",
            "    raise NotImplementedError('Translate and validate this equation before use.')",
            "",
        ]
    if not equations:
        lines += ["# No equations detected."]
    return "\n".join(lines)


def run_oak(result: RosetteResult, mode: str) -> RosetteResult:
    if not result.blocks:
        result.oak_findings.append("HIGH: no text blocks extracted; try OCR/VLM route.")
        result.memory_minus.append("M⁻: empty extraction")
    if not result.equations:
        result.oak_findings.append("LOW: no equations detected by heuristic parser.")
    for eq in result.equations:
        if eq.confidence < 0.9:
            result.oak_findings.append("MEDIUM: equation requires render-diff-repair and dimensional OAK.")
            result.memory_minus.append(f"M⁻: uncertified equation `{eq.latex[:80]}`")
    for claim in result.claims:
        if not claim.evidence_ids:
            result.oak_findings.append("MEDIUM: claim candidate lacks explicit evidence links.")
    if mode == "strict" and not result.oak_findings:
        result.oak_findings.append("INFO: no heuristic OAK finding; this is not proof of correctness.")
    return result


class RosettePipeline:
    def __init__(self, mode: str = "strict") -> None:
        self.mode = mode

    def process(self, input_path: str | Path) -> RosetteResult:
        path, digest = ingest(input_path)
        text = extract_text(path)
        blocks = split_blocks(text, path)
        result = RosetteResult(
            input_path=str(path),
            sha256=digest,
            blocks=blocks,
            equations=extract_equations(blocks),
            claims=build_claims(blocks),
            oak_findings=[],
            memory_minus=[],
        )
        return run_oak(result, self.mode)

    def compile(self, input_path: str | Path, out_dir: str | Path) -> RosetteResult:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        result = self.process(input_path)
        (out / "document.md").write_text("\n\n".join(b.text for b in result.blocks), encoding="utf-8")
        (out / "document.json").write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        (out / "equations.tex").write_text(equations_to_tex(result.equations), encoding="utf-8")
        theory = {"claims": [asdict(c) for c in result.claims], "tristan_links": ["Ω-ROSETTE-T", "OAK", "M⁻", "HGFM", "CVCD"]}
        (out / "theory_graph.json").write_text(json.dumps(theory, indent=2, ensure_ascii=False), encoding="utf-8")
        (out / "code").mkdir(exist_ok=True)
        (out / "code" / "equations.py").write_text(code_from_equations(result.equations), encoding="utf-8")
        (out / "absorption.md").write_text(make_absorption(result), encoding="utf-8")
        (out / "OAK_REPORT.md").write_text(make_oak_report(result), encoding="utf-8")
        (out / "M_MINUS.md").write_text("\n".join(f"- {m}" for m in result.memory_minus), encoding="utf-8")
        return result


def make_absorption(result: RosetteResult) -> str:
    return "\n".join([
        "# Absorption — Ω-ROSETTE-T",
        "",
        f"- Blocs extraits : {len(result.blocks)}",
        f"- Équations détectées : {len(result.equations)}",
        f"- Claims candidats : {len(result.claims)}",
        "",
        "## Questions OAK",
        "1. Les équations sont-elles dimensionnellement cohérentes ?",
        "2. Les claims sont-ils liés à figures/tables/références ?",
        "3. Que peut-on reproduire en code sans données propriétaires ?",
        "4. Quelles extensions Tristan sont nouvelles versus dérivées ?",
    ])


def make_oak_report(result: RosetteResult) -> str:
    lines = ["# OAK Report — Ω-ROSETTE-T", "", f"Input: `{result.input_path}`", f"Blocks: {len(result.blocks)}", f"Equations: {len(result.equations)}", f"Claims: {len(result.claims)}", "", "## Findings"]
    lines += [f"- {finding}" for finding in result.oak_findings] or ["- No findings. Not a proof of correctness."]
    lines += ["", "## Axioms", "- OCR ≠ vérité.", "- Résumé ≠ preuve.", "- Code compilé ≠ modèle validé."]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rosette")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ["ingest", "extract", "compile"]:
        p = sub.add_parser(name)
        p.add_argument("input")
        if name != "ingest":
            p.add_argument("--out", default="out")
        if name == "compile":
            p.add_argument("--mode", choices=["strict", "research", "creative"], default="strict")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "ingest":
        path, digest = ingest(args.input)
        print(f"path={path}")
        print(f"sha256={digest}")
        return 0
    if args.command == "extract":
        path, _ = ingest(args.input)
        blocks = split_blocks(extract_text(path), path)
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "document.md").write_text("\n\n".join(b.text for b in blocks), encoding="utf-8")
        print(f"extracted_blocks={len(blocks)}")
        return 0
    if args.command == "compile":
        result = RosettePipeline(args.mode).compile(args.input, args.out)
        print(f"blocks={len(result.blocks)} equations={len(result.equations)} claims={len(result.claims)}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
