from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .schemas import BBox, Block, ConfidenceTensor, ExtractorRun, SourceRef


PAGE_MARKER = re.compile(r"^\s*---\s*PAGE\s+(\d+)\s*---\s*$", re.IGNORECASE | re.MULTILINE)


@dataclass
class ExtractionBundle:
    text: str
    blocks: list[Block]
    runs: list[ExtractorRun] = field(default_factory=list)


def _kind_for(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("#"):
        return "heading"
    if stripped.lower().startswith("definition:"):
        return "definition"
    return "paragraph"


def split_text_blocks(text: str, path: Path, extractor: str = "text", page: int | None = None, base_offset: int = 0) -> list[Block]:
    blocks: list[Block] = []
    cursor = 0
    for para in [p.strip() for p in text.split("\n\n") if p.strip()]:
        local_start = text.find(para, cursor)
        local_end = local_start + len(para)
        cursor = local_end
        blocks.append(
            Block(
                kind=_kind_for(para),
                text=para,
                source=SourceRef(
                    str(path),
                    page=page,
                    span_start=base_offset + local_start,
                    span_end=base_offset + local_end,
                    extractor=extractor,
                    method="text-block-split",
                ),
                confidence=0.9,
                confidence_tensor=ConfidenceTensor(text=0.9, layout=0.55, theory=0.45),
            )
        )
    return blocks


class TextExtractor:
    name = "text"

    def extract(self, path: Path) -> ExtractionBundle:
        text = path.read_text(encoding="utf-8", errors="replace")
        marker_matches = list(PAGE_MARKER.finditer(text))
        if not marker_matches:
            blocks = split_text_blocks(text, path, extractor=self.name)
            return ExtractionBundle(text=text, blocks=blocks, runs=[ExtractorRun(self.name, "ok", pages=1, blocks=len(blocks))])

        blocks: list[Block] = []
        for idx, match in enumerate(marker_matches):
            page = int(match.group(1))
            start = match.end()
            end = marker_matches[idx + 1].start() if idx + 1 < len(marker_matches) else len(text)
            page_text = text[start:end].strip()
            blocks.extend(split_text_blocks(page_text, path, extractor=self.name, page=page, base_offset=start))
        return ExtractionBundle(
            text=text,
            blocks=blocks,
            runs=[ExtractorRun(self.name, "ok", pages=len(marker_matches), blocks=len(blocks))],
        )


class PyMuPDFExtractor:
    name = "pymupdf"

    def extract(self, path: Path) -> ExtractionBundle:
        try:
            import fitz  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("PDF support requires `pip install -e .[pdf]`") from exc

        doc = fitz.open(path)
        text_pages: list[str] = []
        blocks: list[Block] = []
        global_offset = 0
        for page_index, page in enumerate(doc, start=1):
            page_text = page.get_text("text")
            text_pages.append(page_text)
            raw_blocks = page.get_text("blocks")
            if raw_blocks:
                for raw in raw_blocks:
                    x0, y0, x1, y1, raw_text = raw[:5]
                    para = str(raw_text).strip()
                    if not para:
                        continue
                    local_start = page_text.find(para)
                    local_end = local_start + len(para) if local_start >= 0 else None
                    blocks.append(
                        Block(
                            kind=_kind_for(para),
                            text=para,
                            source=SourceRef(
                                str(path),
                                page=page_index,
                                span_start=global_offset + local_start if local_start >= 0 else None,
                                span_end=global_offset + local_end if local_end is not None else None,
                                bbox=BBox(float(x0), float(y0), float(x1), float(y1)),
                                extractor=self.name,
                                method="pymupdf-blocks",
                            ),
                            confidence=0.88,
                            confidence_tensor=ConfidenceTensor(text=0.88, layout=0.74, theory=0.45),
                        )
                    )
            else:
                blocks.extend(split_text_blocks(page_text, path, extractor=self.name, page=page_index, base_offset=global_offset))
            global_offset += len(page_text) + 2
        text = "\n\n".join(text_pages)
        return ExtractionBundle(text=text, blocks=blocks, runs=[ExtractorRun(self.name, "ok", pages=len(doc), blocks=len(blocks))])


def extract_document(path: Path, extractor: str = "auto") -> ExtractionBundle:
    suffix = path.suffix.lower()
    if extractor == "auto":
        extractor = "pymupdf" if suffix == ".pdf" else "text"
    if extractor == "text":
        return TextExtractor().extract(path)
    if extractor == "pymupdf":
        return PyMuPDFExtractor().extract(path)
    raise ValueError(f"unsupported extractor: {extractor}")
