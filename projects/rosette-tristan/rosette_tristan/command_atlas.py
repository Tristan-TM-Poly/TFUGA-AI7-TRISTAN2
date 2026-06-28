from __future__ import annotations

import argparse
import json
import tomllib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


COMMAND_METADATA: dict[str, dict[str, str]] = {
    "rosette": {"layer": "core", "purpose": "compile text/PDF-like input to Markdown, theory, code and OAK report"},
    "rosette-fidelity": {"layer": "fidelity", "purpose": "emit source refs, fidelity report and theory capsule"},
    "rosette-hyper": {"layer": "hyper_absorption", "purpose": "run consensus, claim graph, equation OAK, code forge, absorption and IP checks"},
    "rosette-render": {"layer": "latex_repair", "purpose": "symbolic LaTeX repair scoring"},
    "rosette-real-render": {"layer": "real_render", "purpose": "render equation PNGs and compare candidate/reference images"},
    "rosette-source-crop": {"layer": "source_crop", "purpose": "compare generated render against source crop image/PDF bbox"},
    "rosette-visual-oak": {"layer": "visual_oak", "purpose": "combine real render and source-crop comparison into one visual OAK report"},
    "rosette-bench": {"layer": "bench", "purpose": "run synthetic OAK smoke benchmark"},
    "rosette-bench-corpus": {"layer": "bench_corpus", "purpose": "create and validate annotated corpus manifests"},
    "rosette-corpus-bench": {"layer": "corpus_bench", "purpose": "execute corpus manifest cases and verify expectations"},
    "rosette-doctor": {"layer": "doctor", "purpose": "audit environment, optional modules and command surface"},
    "rosette-atlas": {"layer": "atlas", "purpose": "list commands, layers, docs and OAK status in one JSON/Markdown atlas"},
}

DOC_HINTS: dict[str, str] = {
    "rosette-render": "docs/RENDER_REPAIR.md",
    "rosette-real-render": "docs/REAL_RENDER.md",
    "rosette-source-crop": "docs/SOURCE_CROP_COMPARE.md",
    "rosette-visual-oak": "docs/VISUAL_OAK.md",
    "rosette-bench": "docs/BENCH_RUNNER.md",
    "rosette-bench-corpus": "docs/BENCH_CORPUS.md",
    "rosette-corpus-bench": "docs/CORPUS_BENCH_RUNNER.md",
    "rosette-doctor": "docs/DOCTOR.md",
    "rosette-atlas": "docs/COMMAND_ATLAS.md",
}


@dataclass
class AtlasCommand:
    name: str
    entrypoint: str
    layer: str
    purpose: str
    docs: str | None


@dataclass
class CommandAtlasReport:
    package_version: str
    command_count: int
    commands: list[AtlasCommand]
    missing_metadata: list[str] = field(default_factory=list)
    missing_docs: list[str] = field(default_factory=list)
    oak_status: str = "atlas_passed_not_certified"
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_version": self.package_version,
            "command_count": self.command_count,
            "commands": [asdict(command) for command in self.commands],
            "missing_metadata": self.missing_metadata,
            "missing_docs": self.missing_docs,
            "oak_status": self.oak_status,
            "warnings": self.warnings,
        }


def default_pyproject_path() -> Path:
    return Path(__file__).resolve().parents[1] / "pyproject.toml"


def load_scripts(pyproject_path: str | Path | None = None) -> tuple[str, dict[str, str]]:
    path = Path(pyproject_path) if pyproject_path is not None else default_pyproject_path()
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    project = data.get("project", {})
    scripts = project.get("scripts", {})
    return str(project.get("version", "unknown")), {str(k): str(v) for k, v in scripts.items()}


def build_command_atlas(pyproject_path: str | Path | None = None) -> CommandAtlasReport:
    version, scripts = load_scripts(pyproject_path)
    commands: list[AtlasCommand] = []
    missing_metadata: list[str] = []
    missing_docs: list[str] = []
    for name in sorted(scripts):
        metadata = COMMAND_METADATA.get(name)
        if metadata is None:
            missing_metadata.append(name)
            metadata = {"layer": "unknown", "purpose": "metadata_missing"}
        docs = DOC_HINTS.get(name)
        if docs is None and name != "rosette":
            missing_docs.append(name)
        commands.append(
            AtlasCommand(
                name=name,
                entrypoint=scripts[name],
                layer=metadata["layer"],
                purpose=metadata["purpose"],
                docs=docs,
            )
        )
    warnings: list[str] = []
    if missing_metadata:
        warnings.append("missing command metadata")
    if missing_docs:
        warnings.append("missing command docs hints")
    oak_status = "atlas_passed_not_certified" if not missing_metadata else "atlas_review_needed"
    return CommandAtlasReport(
        package_version=version,
        command_count=len(commands),
        commands=commands,
        missing_metadata=missing_metadata,
        missing_docs=missing_docs,
        oak_status=oak_status,
        warnings=warnings,
    )


def atlas_markdown(report: CommandAtlasReport) -> str:
    lines = [
        "# Rosette Command Atlas",
        "",
        f"Package version: `{report.package_version}`",
        f"Command count: `{report.command_count}`",
        f"OAK status: `{report.oak_status}`",
        "",
        "| Command | Layer | Purpose | Docs |",
        "|---|---|---|---|",
    ]
    for command in report.commands:
        docs = command.docs or ""
        lines.append(f"| `{command.name}` | `{command.layer}` | {command.purpose} | {docs} |")
    lines.extend([
        "",
        "## OAK lock",
        "",
        "The atlas verifies command registration and documentation hints. It does not prove runtime correctness, PDF fidelity, mathematical equivalence or scientific truth.",
    ])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rosette-atlas")
    parser.add_argument("--pyproject", default=None)
    parser.add_argument("--out", default=None, help="Write atlas JSON to this path")
    parser.add_argument("--markdown", default=None, help="Write atlas Markdown to this path")
    args = parser.parse_args(argv)
    report = build_command_atlas(args.pyproject)
    payload = report.to_dict()
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    if args.markdown:
        md = Path(args.markdown)
        md.parent.mkdir(parents=True, exist_ok=True)
        md.write_text(atlas_markdown(report), encoding="utf-8")
    print(text)
    return 0 if report.oak_status != "atlas_review_needed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
