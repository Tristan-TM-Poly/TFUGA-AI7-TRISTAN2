"""Document ingestion for Ω-AI-TRISTAN-LAB v0.2.

The MVP supports UTF-8 text and Markdown directly. PDF support is optional and
uses pypdf only when installed. This keeps the core package lightweight while
making the PDF path explicit and OAK-safe.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class IngestedDocument:
    """A normalized document ready for chunking or RAG."""

    source_path: str
    title: str
    media_type: str
    text: str
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return bool(self.text.strip()) and not self.warnings


@dataclass(frozen=True)
class ChunkRecord:
    """A chunk with deterministic provenance."""

    id: str
    source_path: str
    start: int
    end: int
    text: str
    metadata: dict[str, str] = field(default_factory=dict)


class DocumentIngestor:
    """Read local text/Markdown/PDF documents into provenance-rich chunks."""

    TEXT_SUFFIXES = {".txt", ".md", ".markdown", ".rst", ".tex", ".py", ".json", ".yaml", ".yml"}

    def ingest_path(self, path: str | Path) -> IngestedDocument:
        path_obj = Path(path)
        suffix = path_obj.suffix.lower()
        if suffix in self.TEXT_SUFFIXES:
            return self._ingest_text(path_obj)
        if suffix == ".pdf":
            return self._ingest_pdf(path_obj)
        return IngestedDocument(
            source_path=str(path_obj),
            title=path_obj.name,
            media_type="unsupported",
            text="",
            warnings=[f"Unsupported file type: {suffix or '<none>'}"],
        )

    def ingest_many(self, paths: Iterable[str | Path]) -> list[IngestedDocument]:
        return [self.ingest_path(path) for path in paths]

    def chunk_document(
        self,
        document: IngestedDocument,
        chunk_size: int = 900,
        overlap: int = 120,
    ) -> list[ChunkRecord]:
        """Chunk text with character offsets and source provenance."""

        text = " ".join(document.text.split())
        if not text:
            return []
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must be >= 0 and smaller than chunk_size")

        chunks: list[ChunkRecord] = []
        step = chunk_size - overlap
        for index, start in enumerate(range(0, len(text), step)):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end]
            chunks.append(
                ChunkRecord(
                    id=f"{Path(document.source_path).name}:{index}",
                    source_path=document.source_path,
                    start=start,
                    end=end,
                    text=chunk_text,
                    metadata={"title": document.title, "media_type": document.media_type},
                )
            )
            if end >= len(text):
                break
        return chunks

    def _ingest_text(self, path: Path) -> IngestedDocument:
        try:
            text = path.read_text(encoding="utf-8")
            warnings: list[str] = []
        except UnicodeDecodeError:
            text = path.read_text(encoding="latin-1")
            warnings = ["Decoded with latin-1 fallback; verify accents and symbols."]
        return IngestedDocument(
            source_path=str(path),
            title=path.name,
            media_type=self._media_type(path.suffix.lower()),
            text=text,
            warnings=warnings,
            metadata={"suffix": path.suffix.lower()},
        )

    def _ingest_pdf(self, path: Path) -> IngestedDocument:
        try:
            from pypdf import PdfReader  # type: ignore
        except Exception:
            return IngestedDocument(
                source_path=str(path),
                title=path.name,
                media_type="application/pdf",
                text="",
                warnings=["PDF ingestion requires optional dependency: pip install .[pdf]"],
                metadata={"suffix": ".pdf"},
            )

        reader = PdfReader(str(path))
        pages: list[str] = []
        page_warnings: list[str] = []
        for page_index, page in enumerate(reader.pages):
            extracted = page.extract_text() or ""
            if not extracted.strip():
                page_warnings.append(f"Page {page_index + 1}: no extractable text; OCR may be required.")
            pages.append(extracted)
        return IngestedDocument(
            source_path=str(path),
            title=path.name,
            media_type="application/pdf",
            text="\n\n".join(pages),
            warnings=page_warnings,
            metadata={"suffix": ".pdf", "pages": str(len(reader.pages))},
        )

    @staticmethod
    def _media_type(suffix: str) -> str:
        return {
            ".md": "text/markdown",
            ".markdown": "text/markdown",
            ".txt": "text/plain",
            ".rst": "text/x-rst",
            ".tex": "text/x-tex",
            ".py": "text/x-python",
            ".json": "application/json",
            ".yaml": "application/yaml",
            ".yml": "application/yaml",
        }.get(suffix, "text/plain")
