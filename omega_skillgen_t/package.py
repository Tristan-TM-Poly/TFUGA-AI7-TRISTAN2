from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import zipfile
from typing import Any

DEFAULT_WRAPPERS = (
    "omega-skillgen",
    "omega-skillgen-bridge",
    "omega-skillgen-benchmark",
    "omega-skillgen-campaign",
    "omega-skillgen-ops",
    "omega-skillgen-ultra",
    "omega-skillgen-evolution",
    "omega-skillgen-civilization",
)


def build_standalone_bundle(
    repo_root: str | Path,
    out_zip: str | Path,
    *,
    skill_dir: str | Path = ".agents/skills/omega-skillgen-t",
    package_dir: str | Path = "omega_skillgen_t",
    wrappers: tuple[str, ...] = DEFAULT_WRAPPERS,
) -> dict[str, Any]:
    repo_root = Path(repo_root)
    skill_dir = repo_root / skill_dir
    package_dir = repo_root / package_dir
    out_zip = Path(out_zip)

    if not (skill_dir / "SKILL.md").exists():
        raise FileNotFoundError(f"missing {skill_dir / 'SKILL.md'}")
    if not package_dir.exists():
        raise FileNotFoundError(f"missing package {package_dir}")

    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="omega-skillgen-package-") as td:
        bundle = Path(td) / "omega-skillgen-t"
        bundle.mkdir(parents=True)
        shutil.copy2(skill_dir / "SKILL.md", bundle / "SKILL.md")
        shutil.copytree(
            package_dir,
            bundle / "omega_skillgen_t",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        (bundle / "scripts").mkdir()
        copied = []
        for name in wrappers:
            source = repo_root / "scripts" / name
            if source.exists():
                shutil.copy2(source, bundle / "scripts" / name)
                copied.append(name)

        manifests = [p for p in bundle.rglob("*") if p.is_file() and p.name.lower() == "skill.md"]
        if len(manifests) != 1:
            raise ValueError(f"standalone bundle must contain exactly one SKILL.md, found {len(manifests)}")

        if out_zip.exists():
            out_zip.unlink()
        with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in bundle.rglob("*"):
                if path.is_file():
                    archive.write(path, arcname=str(Path(bundle.name) / path.relative_to(bundle)))

    with zipfile.ZipFile(out_zip) as archive:
        zip_manifests = [name for name in archive.namelist() if Path(name).name.lower() == "skill.md"]
        if len(zip_manifests) != 1:
            raise ValueError(f"zip must contain exactly one SKILL.md, found {len(zip_manifests)}")

    return {
        "status": "PASS",
        "zip": str(out_zip),
        "bytes": out_zip.stat().st_size,
        "wrappers": copied,
        "skill_manifests": len(zip_manifests),
    }
