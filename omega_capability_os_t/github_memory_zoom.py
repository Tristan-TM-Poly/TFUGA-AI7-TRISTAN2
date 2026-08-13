from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import quote, urlencode
import argparse
import ast
import base64
import json
import os

from .github_memory import (
    AssetObservation,
    CapabilityRequest,
    GitHubMemoryIndex,
    GitHubPRSource,
    PRMemory,
    ReuseBeforeCreateGate,
    _tokens,
)

ZOOM_SCHEMA_VERSION = "0.3.0"


@dataclass(frozen=True)
class SymbolObservation:
    path: str
    qualified_name: str
    kind: str
    line: int


class _SymbolVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.stack: list[str] = []
        self.symbols: list[SymbolObservation] = []
        self.path = ""

    def _visit_named(self, node: ast.AST, name: str, kind: str) -> None:
        qualified = ".".join((*self.stack, name))
        self.symbols.append(SymbolObservation(self.path, qualified, kind, int(getattr(node, "lineno", 0))))
        self.stack.append(name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        self._visit_named(node, node.name, "class")

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self._visit_named(node, node.name, "function" if not self.stack else "method")

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self._visit_named(node, node.name, "async_function" if not self.stack else "async_method")


def extract_python_symbols(source: str, path: str) -> tuple[SymbolObservation, ...]:
    tree = ast.parse(source, filename=path)
    visitor = _SymbolVisitor()
    visitor.path = path
    visitor.visit(tree)
    return tuple(visitor.symbols)


@dataclass(frozen=True)
class ProgressiveRetrievalReceipt:
    schema: str
    request_id: str
    candidate_prs: tuple[str, ...]
    hydrated_prs: tuple[str, ...]
    changed_file_count: int
    symbol_count: int
    errors: tuple[dict[str, str], ...]
    boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProgressiveGitHubRetriever:
    """Zooms into selected PRs and extracts static Python symbols without executing candidate code."""

    def __init__(self, source: GitHubPRSource) -> None:
        self.source = source

    def _detail(self, repository: str, number: int) -> Mapping[str, Any]:
        owner, name = repository.split("/", 1)
        url = f"{self.source.api_base}/repos/{owner}/{name}/pulls/{number}"
        payload = self.source.transport(url)
        if not isinstance(payload, Mapping):
            raise TypeError(f"expected PR detail mapping for #{number}")
        return payload

    def _files(self, repository: str, number: int) -> list[Mapping[str, Any]]:
        owner, name = repository.split("/", 1)
        return self.source._pages(f"/repos/{owner}/{name}/pulls/{number}/files")

    def _file_source(self, repository: str, path: str, ref: str) -> str | None:
        owner, name = repository.split("/", 1)
        safe_path = quote(path, safe="/")
        url = f"{self.source.api_base}/repos/{owner}/{name}/contents/{safe_path}?{urlencode({'ref': ref})}"
        payload = self.source.transport(url)
        if not isinstance(payload, Mapping) or payload.get("type") not in {None, "file"}:
            return None
        if payload.get("encoding") != "base64" or not payload.get("content"):
            return None
        compact = str(payload["content"]).replace("\n", "")
        return base64.b64decode(compact).decode("utf-8", errors="replace")

    def hydrate_refs(
        self,
        index: GitHubMemoryIndex,
        candidate_refs: Iterable[str],
        *,
        request_id: str,
        max_files_per_pr: int = 8,
        extract_symbols: bool = True,
    ) -> ProgressiveRetrievalReceipt:
        """Hydrate an explicit ranked/deduplicated inspection queue.

        This is the bridge used by PR-LLMT: ranking and exact inspection stay
        separate. The caller owns candidate ordering; this method never silently
        re-ranks explicit references with the older lexical search policy.
        """
        if max_files_per_pr < 0:
            raise ValueError("max_files_per_pr must be non-negative")
        refs = tuple(dict.fromkeys(str(ref) for ref in candidate_refs if str(ref)))
        hydrated: list[str] = []
        errors: list[dict[str, str]] = []
        changed_file_count = 0
        symbol_count = 0

        for ref in refs:
            pr = index.prs.get(ref)
            if pr is None:
                errors.append({"ref": ref, "path": "", "error": "KeyError: candidate ref not present in index"})
                continue
            try:
                detail = self._detail(pr.repository, pr.number)
                file_rows = self._files(pr.repository, pr.number)
                filenames = [str(row["filename"]) for row in file_rows if row.get("filename")]
                changed_file_count += len(filenames)
                hydrated_pr = PRMemory.from_github(pr.repository, detail, files=filenames)
                index.add_pr(hydrated_pr)
                hydrated.append(hydrated_pr.ref)

                if not extract_symbols or not hydrated_pr.head_sha:
                    continue
                inspected = 0
                for row in file_rows:
                    path = str(row.get("filename", ""))
                    status = str(row.get("status", ""))
                    if not path.endswith(".py") or status == "removed":
                        continue
                    if inspected >= max_files_per_pr:
                        break
                    inspected += 1
                    try:
                        source_text = self._file_source(pr.repository, path, hydrated_pr.head_sha)
                        if source_text is None:
                            continue
                        for symbol in extract_python_symbols(source_text, path):
                            asset_id = f"symbol:{hydrated_pr.ref}:{path}:{symbol.qualified_name}"
                            index.assets[asset_id] = AssetObservation(
                                asset_id=asset_id,
                                source_ref=hydrated_pr.ref,
                                source_kind="pr_head_python_ast_symbol",
                                label=f"{path}::{symbol.qualified_name}",
                                keywords=_tokens((path, symbol.qualified_name, symbol.kind, hydrated_pr.title)),
                                confidence=0.80,
                                boundary="static AST symbol existence != reusable behavior or semantic equivalence; inspect implementation/tests before reuse",
                            )
                            symbol_count += 1
                    except (SyntaxError, UnicodeError, ValueError, TypeError, RuntimeError) as exc:
                        errors.append({"ref": hydrated_pr.ref, "path": path, "error": f"{type(exc).__name__}: {exc}"})
            except (ValueError, TypeError, RuntimeError) as exc:
                errors.append({"ref": ref, "path": "", "error": f"{type(exc).__name__}: {exc}"})

        return ProgressiveRetrievalReceipt(
            schema=f"omega-github-progressive-retrieval/v{ZOOM_SCHEMA_VERSION}",
            request_id=request_id,
            candidate_prs=refs,
            hydrated_prs=tuple(hydrated),
            changed_file_count=changed_file_count,
            symbol_count=symbol_count,
            errors=tuple(errors),
            boundary=(
                "Progressive hydration improves inspection evidence only. Ranked refs, changed files and AST symbols are candidates, "
                "not semantic equivalence, correctness, test success, or permission to mutate."
            ),
        )

    def hydrate(
        self,
        index: GitHubMemoryIndex,
        request: CapabilityRequest,
        *,
        top_prs: int = 5,
        max_files_per_pr: int = 8,
        extract_symbols: bool = True,
    ) -> ProgressiveRetrievalReceipt:
        """Backward-compatible lexical candidate selection followed by exact hydration."""
        candidates = index.search_prs(request, top_k=max(1, top_prs))
        return self.hydrate_refs(
            index,
            (str(candidate["ref"]) for candidate in candidates),
            request_id=request.request_id,
            max_files_per_pr=max_files_per_pr,
            extract_symbols=extract_symbols,
        )


def _load(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path: str | None, payload: Mapping[str, Any]) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-github-memory-zoom")
    parser.add_argument("index")
    parser.add_argument("request")
    parser.add_argument("--top-prs", type=int, default=5)
    parser.add_argument("--max-files-per-pr", type=int, default=8)
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    parser.add_argument("--without-symbols", action="store_true")
    parser.add_argument("--output-index")
    parser.add_argument("--output-context")
    parser.add_argument("--output-receipt")
    args = parser.parse_args(argv)

    index = GitHubMemoryIndex.from_dict(_load(args.index))
    request = CapabilityRequest.from_dict(_load(args.request))
    source = GitHubPRSource(token=os.getenv(args.token_env) if args.token_env else None)
    receipt = ProgressiveGitHubRetriever(source).hydrate(
        index,
        request,
        top_prs=args.top_prs,
        max_files_per_pr=args.max_files_per_pr,
        extract_symbols=not args.without_symbols,
    )
    context = ReuseBeforeCreateGate(index).compile_context(request)
    _write(args.output_index, index.to_dict())
    _write(args.output_context, context)
    _write(args.output_receipt, receipt.to_dict())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
