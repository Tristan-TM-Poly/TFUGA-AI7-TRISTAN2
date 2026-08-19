"""Local-only AdapterForge for turning repositories into Tristan capabilities.

AdapterForge never clones repositories and never changes the inspected source
tree unless materialize() is explicitly called with an output directory.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]


@dataclass(frozen=True, slots=True)
class RepositoryInspection:
    root: str
    project_name: str | None
    packaging_status: str
    has_pyproject: bool
    has_setup_py: bool
    has_src: bool
    python_files: int
    candidate_packages: tuple[str, ...]
    console_scripts: tuple[str, ...]
    evidence: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AdapterPlan:
    inspection: RepositoryInspection
    plugin_name: str
    manifest: dict[str, Any]
    adapter_source: str
    next_actions: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"inspection": self.inspection.to_dict(), "plugin_name": self.plugin_name, "manifest": self.manifest, "adapter_source": self.adapter_source, "next_actions": list(self.next_actions)}


class AdapterForge:
    def inspect(self, root: str | Path) -> RepositoryInspection:
        path = Path(root).resolve()
        if not path.exists() or not path.is_dir():
            raise FileNotFoundError(path)
        pyproject = path / "pyproject.toml"
        setup_py = path / "setup.py"
        has_src = (path / "src").is_dir()
        project_name: str | None = None
        scripts: tuple[str, ...] = ()
        evidence: list[str] = []
        if pyproject.is_file():
            evidence.append("pyproject.toml")
            if tomllib is not None:
                data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
                project = data.get("project", {})
                project_name = project.get("name")
                scripts = tuple(sorted((project.get("scripts") or {}).keys()))
        if setup_py.is_file():
            evidence.append("setup.py")
        if has_src:
            evidence.append("src/")
        python_files = sum(1 for p in path.rglob("*.py") if ".git" not in p.parts)
        package_roots = path / "src" if has_src else path
        candidates = tuple(sorted(p.name for p in package_roots.iterdir() if p.is_dir() and (p / "__init__.py").is_file() and re.match(r"^[A-Za-z_]\w*$", p.name)))
        if pyproject.is_file() and project_name and candidates:
            status = "package"
        elif pyproject.is_file() or setup_py.is_file() or candidates:
            status = "partial"
        else:
            status = "needs-packaging"
        return RepositoryInspection(str(path), project_name, status, pyproject.is_file(), setup_py.is_file(), has_src, python_files, candidates, scripts, tuple(evidence))

    def plan(self, root: str | Path, *, plugin_name: str | None = None) -> AdapterPlan:
        inspection = self.inspect(root)
        name = plugin_name or inspection.project_name or Path(inspection.root).name.lower().replace("_", "-")
        capability_ids = tuple(f"{name}.cli.{script}" for script in inspection.console_scripts) or (f"{name}.inspect",)
        manifest = {
            "schema": "tristan-capability-manifest/0.1",
            "system": {"id": name, "packaging_status": inspection.packaging_status},
            "capabilities": [{"id": cid, "task": cid.rsplit(".", 1)[-1], "permissions": ["PURE"], "deterministic": False} for cid in capability_ids],
            "evidence": list(inspection.evidence),
        }
        adapter_source = (
            '"""Generated AdapterForge scaffold. Review before enabling execution."""\n\n'
            "class GeneratedTristanPlugin:\n"
            f"    name = {name!r}\n\n"
            "    def capabilities(self):\n"
            f"        return {tuple(capability_ids)!r}\n\n"
            "    def run(self, task, payload):\n"
            "        raise NotImplementedError(\n"
            "            'Adapter generated from static evidence only; map tasks to verified callables first.'\n"
            "        )\n\n"
            "plugin = GeneratedTristanPlugin()\n"
        )
        next_actions = (
            "Map each manifest capability to a verified Python callable.",
            "Add differential/contract tests before enabling runtime execution.",
            "Register the reviewed adapter through tristan.plugins.",
        )
        return AdapterPlan(inspection, name, manifest, adapter_source, next_actions)

    def materialize(self, root: str | Path, output_dir: str | Path, *, plugin_name: str | None = None, overwrite: bool = False) -> tuple[Path, Path]:
        plan = self.plan(root, plugin_name=plugin_name)
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        manifest_path = out / "tristan.manifest.json"
        adapter_path = out / "tristan_adapter.py"
        if not overwrite and (manifest_path.exists() or adapter_path.exists()):
            raise FileExistsError("AdapterForge output already exists; use overwrite=True explicitly.")
        manifest_path.write_text(json.dumps(plan.manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        adapter_path.write_text(plan.adapter_source, encoding="utf-8")
        return manifest_path, adapter_path
