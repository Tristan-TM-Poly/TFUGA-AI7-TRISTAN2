"""Tiny local RAG engine with no external dependencies.

This is a baseline implementation for tests and prototypes. It uses lexical
scoring, not embeddings. Future versions can plug in vector search while
keeping the same public methods.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    id: str
    text: str
    source: str = "memory"


class MiniRAG:
    """Simple chunk store and lexical retriever."""

    def __init__(self) -> None:
        self._chunks: list[Chunk] = []

    def add_text(self, text: str, source: str = "memory", chunk_size: int = 700) -> list[Chunk]:
        """Add text and return created chunks."""

        normalized = " ".join(text.split())
        if not normalized:
            return []
        chunks: list[Chunk] = []
        for index, start in enumerate(range(0, len(normalized), chunk_size)):
            chunk_text = normalized[start : start + chunk_size]
            chunk = Chunk(id=f"{source}:{len(self._chunks)+index}", text=chunk_text, source=source)
            chunks.append(chunk)
        self._chunks.extend(chunks)
        return chunks

    def search(self, query: str, top_k: int = 5) -> list[tuple[Chunk, float]]:
        """Return chunks ranked by cosine similarity over token counts."""

        query_vec = self._vectorize(query)
        if not query_vec:
            return []
        scored: list[tuple[Chunk, float]] = []
        for chunk in self._chunks:
            score = self._cosine(query_vec, self._vectorize(chunk.text))
            if score > 0:
                scored.append((chunk, round(score, 4)))
        return sorted(scored, key=lambda item: item[1], reverse=True)[:top_k]

    def answer_context(self, query: str, top_k: int = 3) -> str:
        """Return a cited context block for downstream answer generation."""

        results = self.search(query, top_k=top_k)
        if not results:
            return "No relevant local context found."
        lines = []
        for rank, (chunk, score) in enumerate(results, start=1):
            lines.append(f"[{rank}] source={chunk.source} score={score}\n{chunk.text}")
        return "\n\n".join(lines)

    @staticmethod
    def _vectorize(text: str) -> Counter[str]:
        tokens = re.findall(r"[a-zA-ZÀ-ÿ0-9_-]+", text.lower())
        stopwords = {"the", "and", "or", "de", "du", "des", "le", "la", "les", "un", "une", "et"}
        return Counter(token for token in tokens if token not in stopwords)

    @staticmethod
    def _cosine(a: Counter[str], b: Counter[str]) -> float:
        common = set(a) & set(b)
        numerator = sum(a[token] * b[token] for token in common)
        norm_a = math.sqrt(sum(value * value for value in a.values()))
        norm_b = math.sqrt(sum(value * value for value in b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return numerator / (norm_a * norm_b)
