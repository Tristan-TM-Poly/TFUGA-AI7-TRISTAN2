"""Validate pyproject script surfaces without importing project modules.

This is a lightweight trigger-boundary validator used by Ω-ACTIONS-T∞.  It
checks that selected ``[project.scripts]`` entries point at repository modules
that actually exist, without installing the project or importing optional
runtime dependencies.
"""
from __future__ import annotations

import argparse
import json
import re
import tomllib
from pathlib import Path
from typing import Iterable

_MODULE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")


def _module_candidates(root: Path, module: str) -> tuple[Path, Path]:
    stem = root.joinpath(*module.split("."))
    return stem.with_suffix(".py"), stem / "__init__.py"


def validate_project_scripts(
    pyproject: str | Path,
    prefixes: Iterable[str] = (),
) -> dict:
    pyproject_path = Path(pyproject)
    root = pyproject_path.parent
    with pyproject_path.open("rb") as handle:
        payload = tomllib.load(handle)

    scripts = payload.get("project", {}).get("scripts", {})
    if not isinstance(scripts, dict):
        scripts = {}

    prefix_tuple = tuple(prefixes)
    selected = {
        str(name): str(target)
        for name, target in scripts.items()
        if not prefix_tuple or any(str(name).startswith(prefix) for prefix in prefix_tuple)
    }

    violations: list[dict[str, str]] = []
    checked: list[dict[str, object]] = []
    if prefix_tuple and not selected:
        violations.append(
            {
                "id": "no-matching-scripts",
                "detail": f"No [project.scripts] entries match prefixes {prefix_tuple!r}",
            }
        )

    for name, target in sorted(selected.items()):
        if ":" not in target:
            violations.append(
                {"id": "invalid-target", "script": name, "detail": target}
            )
            continue
        module, callable_name = (part.strip() for part in target.split(":", 1))
        if not _MODULE_RE.fullmatch(module) or not callable_name:
            violations.append(
                {"id": "invalid-target", "script": name, "detail": target}
            )
            continue
        candidates = _module_candidates(root, module)
        existing = next((path for path in candidates if path.is_file()), None)
        checked.append(
            {
                "script": name,
                "target": target,
                "module": module,
                "callable": callable_name,
                "module_path": str(existing.relative_to(root)) if existing else None,
                "module_exists": existing is not None,
            }
        )
        if existing is None:
            violations.append(
                {
                    "id": "missing-module",
                    "script": name,
                    "detail": f"No repository module found for {module}",
                }
            )

    return {
        "schema": "omega-actions-project-surface/v1",
        "pyproject": str(pyproject_path),
        "prefixes": list(prefix_tuple),
        "selected_script_count": len(selected),
        "checked": checked,
        "violations": violations,
        "status": "PASS" if not violations else "FAIL",
        "oak_limits": [
            "This is a structural repository check, not an import/runtime test.",
            "Domain OAKBench workflows remain authoritative for domain behavior.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-actions-project-surface")
    parser.add_argument("pyproject", nargs="?", default="pyproject.toml")
    parser.add_argument("--prefix", action="append", default=[])
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)

    report = validate_project_scripts(args.pyproject, args.prefix)
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.json_out:
        Path(args.json_out).write_text(rendered, encoding="utf-8")
    print(
        "Ω-ACTIONS project-surface "
        f"status={report['status']} scripts={report['selected_script_count']} "
        f"violations={len(report['violations'])}"
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
