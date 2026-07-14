"""Search backend contracts for Ω-AI-TRISTAN-LAB v0.2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .rag_engine import MiniRAG


@dataclass(frozen=True)
class SearchResult:
    """Backend-neutral search result."""

    id: str
    text: str
    source: str
    score: float


class SearchBackend(Protocol):
    """Protocol for future lexical/vector/hybrid retrieval backends."""

    def add(self, text: str, source: str = "memory") -> None:
        ...

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        ...


class LexicalSearchBackend:
    """Default backend: deterministic lexical search using MiniRAG."""

    def __init__(self) -> None:
        self.rag = MiniRAG()

    def add(self, text: str, source: str = "memory") -> None:
        self.rag.add_text(text, source=source)

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        return [
            SearchResult(id=chunk.id, text=chunk.text, source=chunk.source, score=score)
            for chunk, score in self.rag.search(query, top_k=top_k)
        ]


class NullVectorBackend:
    """Placeholder for future vector stores.

    It fails loudly rather than pretending vector search exists.
    """

    def add(self, text: str, source: str = "memory") -> None:
        raise NotImplementedError("Vector backend is not configured. Use LexicalSearchBackend or plug in one.")

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        raise NotImplementedError("Vector backend is not configured. Use LexicalSearchBackend or plug in one.")
