from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]

DEFAULT_BASELINE = Path("config/omega_ci_admission/pyproject_entrypoint_baseline.json")


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
            names.update(target.id for target in node.targets if isinstance(target, ast.Name))
    return names


def _load_baseline(root: Path, baseline_path: Path | None) -> dict[str, Any]:
    path = baseline_path or DEFAULT_BASELINE
    if not path.is_absolute():
        path = root / path
    if not path.is_file():
        return {
            "present": False,
            "source_commit": None,
            "scope": None,
            "targets": {},
            "path": path.as_posix(),
        }
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("schema") != "omega-python-entrypoint-baseline/1":
        raise ValueError("unsupported entrypoint baseline schema")
    targets = raw.get("targets")
    if not isinstance(targets, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in targets.items()):
        raise ValueError("entrypoint baseline targets must be a string mapping")
    return {
        "present": True,
        "source_commit": str(raw.get("source_commit") or ""),
        "scope": str(raw.get("scope") or ""),
        "targets": dict(targets),
        "path": path.relative_to(root).as_posix() if path.is_relative_to(root) else path.as_posix(),
    }


def _script_from_error(error: str) -> str | None:
    parts = error.split(":", 2)
    if len(parts) < 2 or parts[0] == "project.scripts_not_object":
        return None
    return parts[1]


def validate(root: Path, baseline_path: Path | None = None) -> dict[str, Any]:
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

    unique_errors = sorted(set(errors))
    baseline = _load_baseline(root, baseline_path)
    inherited_errors: list[str] = []
    new_errors: list[str] = []
    for error in unique_errors:
        script_name = _script_from_error(error)
        current_target = scripts.get(script_name) if script_name else None
        if (
            baseline["present"]
            and script_name is not None
            and isinstance(current_target, str)
            and baseline["targets"].get(script_name) == current_target
        ):
            inherited_errors.append(error)
        else:
            new_errors.append(error)

    return {
        "schema": "omega-python-entrypoint-audit/2",
        "valid": not new_errors,
        "repository_clean": not unique_errors,
        "script_count": len(scripts),
        "rows": rows,
        "errors": unique_errors,
        "inherited_errors": inherited_errors,
        "new_errors": new_errors,
        "baseline_present": baseline["present"],
        "baseline_path": baseline["path"],
        "baseline_source_commit": baseline["source_commit"],
        "baseline_scope": baseline["scope"],
        "baseline_target_identity_only": True,
        "inherited_error_is_not_claimed_valid": True,
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
