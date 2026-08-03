from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]


def _module_file(root: Path, module_name: str) -> Path | None:
    relative = Path(*module_name.split("."))
    direct = root / relative.with_suffix(".py")
    package = root / relative / "__init__.py"
    if direct.is_file():
        return direct
    if package.is_file():
        return package
    return None


def _defined_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
    return names


def validate(root: Path) -> dict[str, Any]:
    pyproject = root / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    scripts = data.get("project", {}).get("scripts", {})
    errors: list[str] = []
    rows: list[dict[str, Any]] = []
    if not isinstance(scripts, dict):
        errors.append("project.scripts_not_object")
        scripts = {}
    for script_name, target in sorted(scripts.items()):
        if not isinstance(target, str) or ":" not in target:
            errors.append(f"invalid_target:{script_name}")
            continue
        module_name, attribute = target.split(":", 1)
        module_name = module_name.strip()
        attribute = attribute.strip()
        path = _module_file(root, module_name)
        exists = path is not None
        attribute_present = False
        if path is not None:
            try:
                attribute_present = attribute in _defined_names(path)
            except SyntaxError as exc:
                errors.append(f"syntax_error:{script_name}:{exc.lineno}")
        if not exists:
            errors.append(f"module_missing:{script_name}:{module_name}")
        elif not attribute_present:
            errors.append(f"attribute_missing:{script_name}:{target}")
        rows.append(
            {
                "script_name": script_name,
                "target": target,
                "module_path": None if path is None else path.relative_to(root).as_posix(),
                "module_exists": exists,
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
