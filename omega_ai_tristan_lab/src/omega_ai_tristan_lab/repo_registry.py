"""Repository catalog for the Tristan Python ecosystem.

This module deliberately does not clone, install, or mutate repositories.
It describes the known repositories and reports whether their current Python
distribution is available in the active interpreter.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from importlib import metadata
from typing import Iterable


@dataclass(frozen=True, slots=True)
class RepositorySpec:
    key: str
    full_name: str
    visibility: str
    role: str
    distribution: str | None = None
    package_hint: str | None = None
    packaging_status: str = "unknown"
    default_branch: str = "main"
    notes: str = ""

    @property
    def source_url(self) -> str:
        return f"https://github.com/{self.full_name}"

    @property
    def pip_git_target(self) -> str:
        return f"git+https://github.com/{self.full_name}.git@{self.default_branch}"

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["source_url"] = self.source_url
        data["pip_git_target"] = self.pip_git_target
        return data


@dataclass(frozen=True, slots=True)
class RepositoryHealth:
    key: str
    full_name: str
    status: str
    distribution: str | None
    installed_version: str | None
    packaging_status: str
    message: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


DEFAULT_REPOSITORIES: tuple[RepositorySpec, ...] = (
    RepositorySpec(
        key="pefa",
        full_name="Tristan-TM-Poly/PEFA-FractalEnergySystem",
        visibility="private",
        role="Fractal energy-system research and simulations",
        packaging_status="partial",
        notes="Has src/tests and a pytest-only pyproject; needs project/build metadata before wheel builds.",
    ),
    RepositorySpec(
        key="tfacc",
        full_name="Tristan-TM-Poly/TFACC",
        visibility="private",
        role="Multi-system accelerator / infrastructure collection",
        packaging_status="needs-packaging",
        notes="Top-level repository is a collection of subsystems and does not yet expose a root Python distribution.",
    ),
    RepositorySpec(
        key="tfuga-ai7",
        full_name="Tristan-TM-Poly/TFUGA-AI7-TRISTAN2",
        visibility="public",
        role="Omega/AI7 research tooling and CLI collection",
        distribution="tfuga-ai7-tristan2",
        packaging_status="package",
        notes="Root pyproject already declares a Python distribution and many CLI entry points.",
    ),
    RepositorySpec(
        key="tfug-corpus",
        full_name="Tristan-TM-Poly/Tristan_Tardif-Morency_TFUG",
        visibility="public",
        role="Large TFUG corpus and applied research modules",
        distribution="protein-fold-tristan",
        package_hint="protein_fold_tristan",
        packaging_status="partial",
        notes="Root pyproject currently packages one focused module; the full corpus needs adapters for unified execution.",
    ),
    RepositorySpec(
        key="tfugag",
        full_name="Tristan-TM-Poly/Tristan_Tardif-Morency_TFUGAG",
        visibility="public",
        role="TFUGAG companion repository",
        packaging_status="needs-packaging",
        notes="No root pyproject detected during the v0.3 audit.",
    ),
    RepositorySpec(
        key="omni-core",
        full_name="Tristan-TM-Poly/TTM-TFUGA-AI7-TRISTAN2",
        visibility="public",
        role="OAK-governed omni-core monorepo",
        distribution="tristan-omni-core",
        package_hint="tristan_omni_core",
        packaging_status="package",
        notes="Root pyproject already declares tristan-omni-core and many executable CLIs.",
    ),
)


class RepoRegistry:
    """Read-only registry of repositories participating in TristanLab."""

    def __init__(self, repositories: Iterable[RepositorySpec] = DEFAULT_REPOSITORIES):
        self._repositories = tuple(repositories)
        self._by_key = {repo.key: repo for repo in self._repositories}
        self._by_full_name = {repo.full_name: repo for repo in self._repositories}

    def all(self) -> tuple[RepositorySpec, ...]:
        return self._repositories

    def get(self, key_or_full_name: str) -> RepositorySpec:
        if key_or_full_name in self._by_key:
            return self._by_key[key_or_full_name]
        if key_or_full_name in self._by_full_name:
            return self._by_full_name[key_or_full_name]
        raise KeyError(f"Unknown Tristan repository: {key_or_full_name}")

    def doctor(self) -> tuple[RepositoryHealth, ...]:
        checks: list[RepositoryHealth] = []
        for repo in self._repositories:
            if not repo.distribution:
                checks.append(
                    RepositoryHealth(
                        key=repo.key,
                        full_name=repo.full_name,
                        status="needs-packaging",
                        distribution=None,
                        installed_version=None,
                        packaging_status=repo.packaging_status,
                        message="No installable root distribution is registered yet.",
                    )
                )
                continue

            try:
                version = metadata.version(repo.distribution)
            except metadata.PackageNotFoundError:
                checks.append(
                    RepositoryHealth(
                        key=repo.key,
                        full_name=repo.full_name,
                        status="not-installed",
                        distribution=repo.distribution,
                        installed_version=None,
                        packaging_status=repo.packaging_status,
                        message=f"Python distribution {repo.distribution!r} is not installed in this interpreter.",
                    )
                )
            else:
                checks.append(
                    RepositoryHealth(
                        key=repo.key,
                        full_name=repo.full_name,
                        status="installed",
                        distribution=repo.distribution,
                        installed_version=version,
                        packaging_status=repo.packaging_status,
                        message="Distribution is importable from the active Python environment.",
                    )
                )
        return tuple(checks)
