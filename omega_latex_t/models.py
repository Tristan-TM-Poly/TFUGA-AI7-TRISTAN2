from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Mapping


class NodeKind(str, Enum):
    SECTION = "section"
    PARAGRAPH = "paragraph"
    DEFINITION = "definition"
    AXIOM = "axiom"
    CONJECTURE = "conjecture"
    LEMMA = "lemma"
    PROPOSITION = "proposition"
    THEOREM = "theorem"
    COROLLARY = "corollary"
    PROOF = "proof"
    PROOF_SKETCH = "proof_sketch"
    EQUATION = "equation"
    ALGORITHM = "algorithm"
    EXPERIMENT = "experiment"
    DATASET = "dataset"
    RESULT = "result"
    FIGURE = "figure"
    TABLE = "table"
    CLAIM = "claim"
    WARNING = "warning"
    OPEN_QUESTION = "open_question"
    COUNTEREXAMPLE = "counterexample"
    APPENDIX = "appendix"


@dataclass(frozen=True)
class Source:
    id: str
    citation: str
    locator: str = ""
    sha256: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "Source":
        return cls(id=str(data["id"]), citation=str(data.get("citation", "")), locator=str(data.get("locator", "")), sha256=str(data.get("sha256", "")), metadata=dict(data.get("metadata", {})))


@dataclass(frozen=True)
class SymbolSpec:
    symbol: str
    meaning: str
    scope: str = "global"
    unit: str = ""

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "SymbolSpec":
        return cls(symbol=str(data["symbol"]), meaning=str(data.get("meaning", "")), scope=str(data.get("scope", "global")), unit=str(data.get("unit", "")))


@dataclass(frozen=True)
class Node:
    id: str
    kind: NodeKind
    content: str
    title: str = ""
    status: str = "draft"
    dependencies: tuple[str, ...] = ()
    sources: tuple[str, ...] = ()
    source_locators: Mapping[str, str] = field(default_factory=dict)
    symbols: tuple[SymbolSpec, ...] = ()
    result_key: str = ""
    dimension_lhs: str = ""
    dimension_rhs: str = ""
    math_ir: Mapping[str, Any] = field(default_factory=dict)
    figure_ir: Mapping[str, Any] = field(default_factory=dict)
    min_depth: int | None = None
    max_depth: int | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "Node":
        min_depth = data.get("min_depth"); max_depth = data.get("max_depth")
        return cls(id=str(data["id"]), kind=NodeKind(str(data["kind"])), content=str(data.get("content", "")), title=str(data.get("title", "")), status=str(data.get("status", "draft")), dependencies=tuple(str(x) for x in data.get("dependencies", ())), sources=tuple(str(x) for x in data.get("sources", ())), source_locators={str(k): str(v) for k, v in dict(data.get("source_locators", {})).items()}, symbols=tuple(SymbolSpec.from_mapping(x) for x in data.get("symbols", ())), result_key=str(data.get("result_key", "")), dimension_lhs=str(data.get("dimension_lhs", "")), dimension_rhs=str(data.get("dimension_rhs", "")), math_ir=dict(data.get("math_ir", {})), figure_ir=dict(data.get("figure_ir", {})), min_depth=None if min_depth is None else int(min_depth), max_depth=None if max_depth is None else int(max_depth), metadata=dict(data.get("metadata", {})))


@dataclass(frozen=True)
class DocumentMeta:
    title: str
    author: str = ""
    template: str = "research-paper"
    depth: int = 3
    language: str = "en"
    date: str = ""

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "DocumentMeta":
        return cls(title=str(data.get("title", "Untitled")), author=str(data.get("author", "")), template=str(data.get("template", "research-paper")), depth=int(data.get("depth", 3)), language=str(data.get("language", "en")), date=str(data.get("date", "")))


@dataclass(frozen=True)
class DocumentIR:
    meta: DocumentMeta
    nodes: tuple[Node, ...]
    sources: tuple[Source, ...] = ()
    results: Mapping[str, Any] = field(default_factory=dict)
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "DocumentIR":
        return cls(meta=DocumentMeta.from_mapping(data.get("meta", {})), nodes=tuple(Node.from_mapping(x) for x in data.get("nodes", ())), sources=tuple(Source.from_mapping(x) for x in data.get("sources", ())), results=dict(data.get("results", {})), provenance=dict(data.get("provenance", {})))

    def to_mapping(self) -> dict[str, Any]:
        def clean(value: Any) -> Any:
            if isinstance(value, Enum): return value.value
            if isinstance(value, tuple): return [clean(x) for x in value]
            if isinstance(value, dict): return {str(k): clean(v) for k, v in value.items()}
            if hasattr(value, "__dataclass_fields__"): return clean(asdict(value))
            return value
        return clean(self)

    def semantic_hash(self) -> str:
        payload = json.dumps(self.to_mapping(), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return sha256(payload).hexdigest()

    def with_depth(self, depth: int) -> "DocumentIR":
        return replace(self, meta=replace(self.meta, depth=int(depth)))
