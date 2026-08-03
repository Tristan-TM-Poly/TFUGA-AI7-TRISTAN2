from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]


def _module_path(root: Path, module_name: str) -> Path | None:
    relative = Path(*module_name.split("."))
    for candidate in (root / relative.with_suffix(".py"), root / relative / "__init__.py"):
        if candidate.is_file():
            return candidate
    return None


def _top_level_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.ImportFrom):
            names.update(alias.asname or alias.name for alias in node.names)
        elif isinstance(node, ast.Assign):
            names.update(
                target.id
                for target in node.targets
                if isinstance(target, ast.Name)
            )
    return names


def validate(root: Path) -> dict[str, Any]:
    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    scripts = data.get("project", {}).get("scripts", {})
    errors: list[str] = []
    rows: list[dict[str, Any]] = []
    if not isinstance(scripts, dict):
        scripts = {}
        errors.append("project.scripts_not_object")
    for script_name, target in sorted(scripts.items()):
        if not isinstance(target, str) or target.count(":") != 1:
            errors.append(f"invalid_target:{script_name}")
            continue
        module_name, attribute = (part.strip() for part in target.split(":", 1))
        module_path = _module_path(root, module_name)
        attribute_present = False
        if module_path is None:
            errors.append(f"module_missing:{script_name}:{module_name}")
        else:
            try:
                attribute_present = attribute in _top_level_names(module_path)
            except SyntaxError as exc:
                errors.append(f"module_syntax_error:{script_name}:{exc.lineno}")
            if not attribute_present:
                errors.append(f"attribute_missing:{script_name}:{target}")
        rows.append(
            {
                "script_name": script_name,
                "target": target,
                "module_path": None if module_path is None else module_path.relative_to(root).as_posix(),
                "module_exists": module_path is not None,
                "attribute_present_statically": attribute_present,
                "module_imported": False,
            }
        )
    return {
        "schema": "omega-python-entrypoint-audit/1",
        "valid": not errors,
        "script_count": len(scripts),
        "rows": rows,
        "errors": sorted(set(errors)),
        "static_validation_only": True,
        "module_imported": False,
        "external_action_performed": False,
    }


def main() -> int:
    result = validate(Path.cwd())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
