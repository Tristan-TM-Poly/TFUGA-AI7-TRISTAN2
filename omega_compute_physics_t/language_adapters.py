"""Static multi-language source adapters for Omega Compute Physics R0.6.

Python receives AST-level analysis. Other common code extensions receive a
bounded lexical structural fingerprint so they can participate in fleet
inventory immediately. Lexical fingerprints are explicitly weaker than parser-
or compiler-derived IR and must not be promoted to semantic/runtime claims.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any, Protocol, Sequence

from .complexity_ir import compile_source_ir


@dataclass(frozen=True)
class SourceGenome:
    path: str
    language: str
    loc: int
    function_like_blocks: int
    loop_tokens: int
    branch_tokens: int
    call_like_tokens: int
    allocation_tokens: int
    max_brace_depth: int
    parser: str
    confidence: str
    status: str = "multi-language-static-source-genome"
    oak_warning: str = (
        "Non-Python lexical counts are structural planning hints only. They do not "
        "establish semantics, runtime cost, memory traffic or asymptotic complexity."
    )

    def vector(self) -> tuple[float, ...]:
        return tuple(float(value) for value in (
            self.loc,
            self.function_like_blocks,
            self.loop_tokens,
            self.branch_tokens,
            self.call_like_tokens,
            self.allocation_tokens,
            self.max_brace_depth,
        ))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SourceAdapter(Protocol):
    language: str
    extensions: tuple[str, ...]

    def scan(self, source: str, *, path: str) -> SourceGenome: ...


class PythonAdapter:
    language = "python"
    extensions = (".py",)

    def scan(self, source: str, *, path: str) -> SourceGenome:
        functions = compile_source_ir(source, module=path)
        return SourceGenome(
            path=path,
            language=self.language,
            loc=len(source.splitlines()),
            function_like_blocks=len(functions),
            loop_tokens=sum(row.op_count("LOOP") for row in functions),
            branch_tokens=sum(row.op_count("BRANCH") for row in functions),
            call_like_tokens=sum(row.op_count("CALL") for row in functions),
            allocation_tokens=sum(row.op_count("ALLOC") for row in functions),
            max_brace_depth=max((row.max_loop_depth for row in functions), default=0),
            parser="python-ast",
            confidence="syntax-aware",
        )


class LexicalCodeAdapter:
    def __init__(self, language: str, extensions: Sequence[str]) -> None:
        self.language = language
        self.extensions = tuple(extensions)

    @staticmethod
    def _count(pattern: str, source: str) -> int:
        return len(re.findall(pattern, source, flags=re.MULTILINE))

    def scan(self, source: str, *, path: str) -> SourceGenome:
        depth = 0
        max_depth = 0
        for char in source:
            if char == "{":
                depth += 1
                max_depth = max(max_depth, depth)
            elif char == "}":
                depth = max(0, depth - 1)
        function_like = self._count(r"\b(?:def|fn|func|function)\s+[A-Za-z_]\w*|[A-Za-z_]\w*\s*\([^;{}]*\)\s*\{", source)
        loops = self._count(r"\b(?:for|while|loop)\b", source)
        branches = self._count(r"\b(?:if|else\s+if|elif|switch|match|case)\b", source)
        calls = self._count(r"\b[A-Za-z_]\w*\s*\(", source)
        allocations = self._count(r"\b(?:new|malloc|calloc|realloc|make|Box::new|Vec::new)\b", source)
        return SourceGenome(
            path=path,
            language=self.language,
            loc=len(source.splitlines()),
            function_like_blocks=function_like,
            loop_tokens=loops,
            branch_tokens=branches,
            call_like_tokens=calls,
            allocation_tokens=allocations,
            max_brace_depth=max_depth,
            parser="bounded-lexical-heuristic",
            confidence="heuristic",
        )


class LanguageAdapterRegistry:
    def __init__(self) -> None:
        self._by_extension: dict[str, SourceAdapter] = {}

    def register(self, adapter: SourceAdapter) -> None:
        seen: set[str] = set()
        for extension in adapter.extensions:
            key = extension.lower()
            if key in seen:
                continue
            seen.add(key)
            if key in self._by_extension:
                raise ValueError(f"adapter already registered for {key}")
            self._by_extension[key] = adapter

    def adapter_for(self, path: str) -> SourceAdapter | None:
        lower = path.lower()
        matches = [ext for ext in self._by_extension if lower.endswith(ext)]
        if not matches:
            return None
        return self._by_extension[max(matches, key=len)]

    def scan(self, source: str, *, path: str) -> SourceGenome | None:
        adapter = self.adapter_for(path)
        return None if adapter is None else adapter.scan(source, path=path)

    def supported_extensions(self) -> tuple[str, ...]:
        return tuple(sorted(self._by_extension))


def default_language_registry() -> LanguageAdapterRegistry:
    registry = LanguageAdapterRegistry()
    registry.register(PythonAdapter())
    registry.register(LexicalCodeAdapter("c", (".c", ".h")))
    registry.register(LexicalCodeAdapter("cpp", (".cc", ".cpp", ".cxx", ".hpp", ".hh")))
    registry.register(LexicalCodeAdapter("javascript", (".js", ".mjs", ".cjs")))
    registry.register(LexicalCodeAdapter("typescript", (".ts", ".tsx")))
    registry.register(LexicalCodeAdapter("rust", (".rs",)))
    registry.register(LexicalCodeAdapter("go", (".go",)))
    registry.register(LexicalCodeAdapter("java", (".java",)))
    registry.register(LexicalCodeAdapter("csharp", (".cs",)))
    registry.register(LexicalCodeAdapter("julia", (".jl",)))
    registry.register(LexicalCodeAdapter("r", (".r",)))
    registry.register(LexicalCodeAdapter("shell", (".sh", ".bash")))
    return registry
