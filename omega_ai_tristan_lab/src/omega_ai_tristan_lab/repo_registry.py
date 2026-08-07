"""Repository catalog and maturity doctor for the Tristan Python ecosystem."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from importlib import metadata
from typing import Any, Iterable


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
    adapter_branch: str | None = None
    adapter_commit: str | None = None
    runtime_capabilities: tuple[str, ...] = ()

    @property
    def source_url(self) -> str:
        return f"https://github.com/{self.full_name}"

    @property
    def pip_git_target(self) -> str:
        return f"git+https://github.com/{self.full_name}.git@{self.default_branch}"

    @property
    def pinned_adapter_target(self) -> str | None:
        if not self.adapter_commit:
            return None
        return f"git+https://github.com/{self.full_name}.git@{self.adapter_commit}"

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["source_url"] = self.source_url
        data["pip_git_target"] = self.pip_git_target
        data["pinned_adapter_target"] = self.pinned_adapter_target
        return data


@dataclass(frozen=True, slots=True)
class RepositoryHealth:
    key: str
    full_name: str
    status: str
    distribution: str | None
    installed_version: str | None
    packaging_status: str
    packaging_score: float
    message: str
    next_actions: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


DEFAULT_REPOSITORIES: tuple[RepositorySpec, ...] = (
    RepositorySpec(
        "pefa",
        "Tristan-TM-Poly/PEFA-FractalEnergySystem",
        "private",
        "Fractal energy-system research and simulations",
        distribution="pefa-fractal-energy-system",
        package_hint="pefa_omega_em2",
        packaging_status="adapter-candidate",
        notes="R0.1 adapter branch adds project metadata, a Tristan plugin, manifest, tests, and cross-repository CI. Promotion to main remains review-gated.",
        adapter_branch="feat/tristan-runtime-adapter-r01",
        adapter_commit="32b82d5d9818bfdd514eabf9e6ffefc520cc9260",
        runtime_capabilities=("pefa-omega-em2.cvcd-extract", "pefa-omega-em2.cvcd-expand"),
    ),
    RepositorySpec(
        "tfacc",
        "Tristan-TM-Poly/TFACC",
        "private",
        "Multi-system accelerator / infrastructure collection",
        packaging_status="needs-packaging",
        notes="Top-level repository is a collection of subsystems and does not yet expose a root Python distribution.",
    ),
    RepositorySpec(
        "tfuga-ai7",
        "Tristan-TM-Poly/TFUGA-AI7-TRISTAN2",
        "public",
        "Omega/AI7 research tooling and CLI collection",
        distribution="tfuga-ai7-tristan2",
        packaging_status="package",
        notes="Root distribution exists; Ω-AI-TRISTAN-LAB is being developed as an isolated subpackage/runtime.",
        adapter_branch="omega-ai-tristan-lab",
        adapter_commit="54783617bd732ef03f20608f67d2432e4deb9b00",
        runtime_capabilities=("tristan.idea.analyze",),
    ),
    RepositorySpec(
        "tfug-corpus",
        "Tristan-TM-Poly/Tristan_Tardif-Morency_TFUG",
        "public",
        "Large TFUG corpus and applied research modules",
        distribution="protein-fold-tristan",
        package_hint="protein_fold_tristan",
        packaging_status="partial",
        notes="Root pyproject currently packages one focused module; the full corpus needs adapters for unified execution.",
    ),
    RepositorySpec(
        "tfugag",
        "Tristan-TM-Poly/Tristan_Tardif-Morency_TFUGAG",
        "public",
        "TFUGAG companion repository",
        packaging_status="needs-packaging",
        notes="No root pyproject detected during the runtime audit.",
    ),
    RepositorySpec(
        "omni-core",
        "Tristan-TM-Poly/TTM-TFUGA-AI7-TRISTAN2",
        "public",
        "OAK-governed omni-core monorepo",
        distribution="tristan-omni-core",
        package_hint="tristan_omni_core",
        packaging_status="adapter-candidate",
        notes="Existing package plus R0.1 Tristan Runtime adapter branch. Adapter promotion remains review-gated.",
        adapter_branch="feat/tristan-runtime-adapter-r01",
        adapter_commit="29e77ad2e1214eb536043b31670071f5079285a5",
        runtime_capabilities=("tristan-omni-core.evidence-to-idea", "tristan-omni-core.valuation-assess"),
    ),
)


class RepoRegistry:
    """Read-only registry of repositories participating in TristanLab."""

    _SCORES = {
        "package": 1.0,
        "adapter-candidate": 0.85,
        "partial": 0.55,
        "needs-packaging": 0.2,
        "unknown": 0.0,
    }

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

    def _actions(self, repo: RepositorySpec, installed: bool) -> tuple[str, ...]:
        actions: list[str] = []
        if repo.packaging_status == "adapter-candidate":
            actions.append("Require exact-head adapter CI and human review before promoting the adapter to the default branch.")
        elif repo.packaging_status != "package":
            actions.append("Generate/review a root Python distribution and tristan.plugins adapter.")
        if repo.distribution and not installed:
            actions.append(f"Build and install a pinned wheel for {repo.distribution}.")
        if not repo.runtime_capabilities:
            actions.append("Publish a capability manifest with tests and OAK evidence.")
        else:
            actions.append("Retain capability-level tests, provenance, and OAK non-claims during integration.")
        return tuple(actions)

    def doctor(self) -> tuple[RepositoryHealth, ...]:
        checks: list[RepositoryHealth] = []
        for repo in self._repositories:
            score = self._SCORES.get(repo.packaging_status, 0.0)
            if not repo.distribution:
                checks.append(
                    RepositoryHealth(
                        repo.key,
                        repo.full_name,
                        "needs-packaging",
                        None,
                        None,
                        repo.packaging_status,
                        score,
                        "No installable root distribution is registered yet.",
                        self._actions(repo, False),
                    )
                )
                continue
            try:
                version = metadata.version(repo.distribution)
            except metadata.PackageNotFoundError:
                checks.append(
                    RepositoryHealth(
                        repo.key,
                        repo.full_name,
                        "not-installed",
                        repo.distribution,
                        None,
                        repo.packaging_status,
                        score,
                        f"Python distribution {repo.distribution!r} is not installed in this interpreter.",
                        self._actions(repo, False),
                    )
                )
            else:
                checks.append(
                    RepositoryHealth(
                        repo.key,
                        repo.full_name,
                        "installed",
                        repo.distribution,
                        version,
                        repo.packaging_status,
                        score,
                        "Distribution metadata is available in the active Python environment.",
                        self._actions(repo, True),
                    )
                )
        return tuple(checks)

    def doctor_summary(self) -> dict[str, Any]:
        health = self.doctor()
        total = len(health)
        return {
            "repositories": total,
            "installed": sum(item.status == "installed" for item in health),
            "packaged": sum(item.packaging_status == "package" for item in health),
            "adapter_candidates": sum(item.packaging_status == "adapter-candidate" for item in health),
            "partial": sum(item.packaging_status == "partial" for item in health),
            "needs_packaging": sum(item.packaging_status == "needs-packaging" for item in health),
            "registered_runtime_capabilities": sum(len(repo.runtime_capabilities) for repo in self._repositories),
            "packaging_maturity": round(sum(item.packaging_score for item in health) / total if total else 0.0, 3),
            "oak_rule": "Packaging and adapter maturity are integration evidence, not proof that scientific capabilities are correct.",
        }
