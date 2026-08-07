from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

from .audit import duplicate_candidates
from .index import append_snapshot, write_longitudinal_reports
from .models import SummaryNode
from .render import write_bundle, write_operational_views
from .summarizer import SummaryEngine, deterministic_timestamp


@dataclass(frozen=True)
class RepositorySpec:
    root: str
    name: str | None = None

    @property
    def path(self) -> Path:
        return Path(self.root).resolve()

    @property
    def display_name(self) -> str:
        return self.name or self.path.name


@dataclass
class CorpusBundle:
    schema_version: str
    generated_at: str
    depth: int
    audience: str
    repositories: list[dict]
    totals: dict
    gaps: list[dict]
    duplicate_candidates: list[dict]
    cross_repo_links: list[dict]
    fingerprint: str

    def to_dict(self) -> dict:
        return asdict(self)


def load_manifest(path: str | Path) -> list[RepositorySpec]:
    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    entries = payload.get("repositories", payload) if isinstance(payload, dict) else payload
    if not isinstance(entries, list):
        raise ValueError("manifest must contain a repository list")
    specs: list[RepositorySpec] = []
    base = source.resolve().parent
    for item in entries:
        if isinstance(item, str):
            root = Path(item)
            name = None
        elif isinstance(item, dict) and item.get("root"):
            root = Path(str(item["root"]))
            name = item.get("name")
        else:
            raise ValueError("each repository entry must be a path string or {root,name}")
        if not root.is_absolute():
            root = base / root
        specs.append(RepositorySpec(str(root), str(name) if name else None))
    return specs


def discover_local_repositories(workspace: str | Path, *, include_workspace: bool = True) -> list[RepositorySpec]:
    workspace = Path(workspace).resolve()
    roots: list[Path] = []
    if include_workspace and _looks_like_repository(workspace):
        roots.append(workspace)
    if workspace.is_dir():
        for child in sorted(workspace.iterdir(), key=lambda p: p.name.casefold()):
            if child.is_dir() and _looks_like_repository(child):
                roots.append(child)
    dedup: dict[str, Path] = {str(path.resolve()): path for path in roots}
    return [RepositorySpec(str(path), path.name) for path in dedup.values()]


def _looks_like_repository(path: Path) -> bool:
    return (path / ".git").exists() or (path / "pyproject.toml").exists() or (path / "package.json").exists() or (path / "Cargo.toml").exists() or (path / "README.md").exists()


def _corpus_fingerprint(repositories: list[dict], depth: int, audience: str) -> str:
    payload = [{"name": r["name"], "fingerprint": r["fingerprint"]} for r in repositories]
    raw = json.dumps({"repositories": payload, "depth": depth, "audience": audience}, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _cross_repo_duplicate_candidates(repository_records: list[dict], threshold: float = 0.72) -> tuple[list[dict], list[dict]]:
    nodes: list[SummaryNode] = []
    for record in repository_records:
        for item in record.get("systems", []):
            node_id = f"{record['name']}::{item['path']}"
            nodes.append(SummaryNode(node_id, "system", node_id, item["title"], item["one_line"], item["status"]))
    raw = duplicate_candidates(nodes, threshold=threshold)
    cross = [item for item in raw if item["left"].split("::", 1)[0] != item["right"].split("::", 1)[0]]
    links = [
        {
            "source": item["left"],
            "target": item["right"],
            "relation": "NEAR_DUPLICATE_CANDIDATE",
            "confidence": item["similarity"],
            "authority": "review_only",
        }
        for item in cross
    ]
    return cross, links


class CorpusSummaryEngine:
    def __init__(self, repositories: Iterable[RepositorySpec], *, max_files: int = 20000) -> None:
        self.repositories = list(repositories)
        self.max_files = max_files

    def generate(self, *, depth: int = 4, audience: str = "tristan") -> CorpusBundle:
        records: list[dict] = []
        all_gaps: list[dict] = []
        totals = {"repositories": 0, "systems": 0, "implemented": 0, "tested": 0, "documents": 0}
        for spec in sorted(self.repositories, key=lambda s: s.display_name.casefold()):
            if not spec.path.exists():
                records.append({"name": spec.display_name, "available": False, "reason": "path_missing"})
                continue
            bundle = SummaryEngine(spec.path, max_files=self.max_files).generate(depth=depth, audience=audience)
            systems = [node for node in bundle.nodes if node.kind == "system"]
            record = {
                "name": spec.display_name,
                "available": True,
                "fingerprint": bundle.cache_fingerprint,
                "health": bundle.health,
                "systems": [
                    {
                        "path": n.path,
                        "title": n.title,
                        "one_line": n.one_line,
                        "status": n.status,
                        "metrics": n.metrics,
                    }
                    for n in systems
                ],
                "gap_count": len(bundle.gaps),
            }
            records.append(record)
            totals["repositories"] += 1
            totals["systems"] += len(systems)
            totals["implemented"] += sum(bool(n.metrics.get("implemented")) for n in systems)
            totals["tested"] += sum(bool(n.metrics.get("tested")) for n in systems)
            totals["documents"] += sum(int(n.metrics.get("documents", 0)) for n in systems)
            all_gaps.extend({**gap, "repository": spec.display_name} for gap in bundle.gaps)
        available = [record for record in records if record.get("available")]
        duplicates, links = _cross_repo_duplicate_candidates(available)
        return CorpusBundle(
            schema_version="1.0.0",
            generated_at=deterministic_timestamp(),
            depth=depth,
            audience=audience,
            repositories=records,
            totals=totals,
            gaps=sorted(all_gaps, key=lambda x: (x.get("priority", 99), x.get("repository", ""), x.get("system", ""))),
            duplicate_candidates=duplicates,
            cross_repo_links=links,
            fingerprint=_corpus_fingerprint(available, depth, audience),
        )

    def write(self, output_dir: str | Path, *, depth: int = 4, audience: str = "tristan", emit_repository_views: bool = True) -> CorpusBundle:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        bundle = self.generate(depth=depth, audience=audience)
        if emit_repository_views:
            for spec in self.repositories:
                if not spec.path.exists():
                    continue
                repo_bundle = SummaryEngine(spec.path, max_files=self.max_files).generate(depth=depth, audience=audience)
                repo_out = output / "repositories" / _safe_name(spec.display_name)
                write_bundle(repo_bundle, repo_out)
                if depth >= 3:
                    write_operational_views(repo_bundle, repo_out)
        corpus_json = output / "CORPUS_SUMMARY.json"
        corpus_json.write_text(
            json.dumps(bundle.to_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        (output / "CORPUS_SUMMARY.md").write_text(render_corpus_markdown(bundle), encoding="utf-8")

        # Zero-touch history: logically append-only and idempotent by fingerprint.
        index_path = output / "CORPUS_INDEX.json"
        append_snapshot(index_path, bundle.to_dict())
        write_longitudinal_reports(index_path, output / "longitudinal")
        return bundle


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_." else "-" for ch in value).strip("-") or "repo"


def render_corpus_markdown(bundle: CorpusBundle) -> str:
    lines = [
        "# Ω-SUMMARY-FRACTAL — Corpus",
        "",
        f"- **Depth:** D{bundle.depth}",
        f"- **Audience:** `{bundle.audience}`",
        f"- **Fingerprint:** `{bundle.fingerprint}`",
        f"- **Repositories available:** {bundle.totals['repositories']}",
        f"- **Systems observed:** {bundle.totals['systems']}",
        "- **Historique zéro-touch:** `CORPUS_INDEX.json` + `longitudinal/` dans le même répertoire de sortie",
        "",
        "## Repositories",
        "",
        "| Repository | Available | Systems | Gaps | Fingerprint |",
        "|---|---:|---:|---:|---|",
    ]
    for record in bundle.repositories:
        lines.append(f"| `{record['name']}` | {'yes' if record.get('available') else 'no'} | {len(record.get('systems', []))} | {record.get('gap_count', 0)} | `{record.get('fingerprint', '-')}` |")
    lines += ["", "## Cross-repository candidates", ""]
    lines += [f"- `{item['left']}` ↔ `{item['right']}` — {item['similarity']:.2f}, review only." for item in bundle.duplicate_candidates[:100]] or ["_No cross-repository near-duplicate candidate above the current heuristic threshold._"]
    lines += [
        "",
        "## OAK boundary",
        "",
        "This corpus view reports observable repository structure. Cross-repository similarity and longitudinal crystallization are review/audit signals only; they do not prove identity, novelty, scientific validity, ownership, patentability, safety, commercial value or progress.",
        "",
    ]
    return "\n".join(lines)
