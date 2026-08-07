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
        notes="R0.2 driver is exact-pinned and four-repository CI verified; promotion to main remains review-gated.",
        adapter_branch="feat/tristan-runtime-adapter-r01",
        adapter_commit="1e72e4619c3fb2b2c175f23ae8053d752a709621",
        runtime_capabilities=("pefa-omega-em2.cvcd-extract", "pefa-omega-em2.cvcd-expand"),
    ),
    RepositorySpec(
        "tfacc",
        "Tristan-TM-Poly/TFACC",
        "private",
        "Multi-system accelerator / infrastructure collection",
        packaging_status="needs-packaging",
        notes="Real ai7_auto kernels exist, but no root adapter is promoted until dependency boundaries are modeled honestly.",
    ),
    RepositorySpec(
        "tfuga-ai7",
        "Tristan-TM-Poly/TFUGA-AI7-TRISTAN2",
        "public",
        "Omega/AI7 research tooling and shared Tristan Runtime host",
        distribution="tfuga-ai7-tristan2",
        packaging_status="package",
        notes="The isolated omega_ai_tristan_lab subpackage is the shared capability runtime; exact f4f1968 runtime was exercised by four-repository CI.",
        adapter_branch="omega-ai-tristan-lab",
        adapter_commit="f4f1968b6fd63ec4c2167f79d29701d92e65afa7",
        runtime_capabilities=("tristan.idea.analyze",),
    ),
    RepositorySpec(
        "tfug-corpus",
        "Tristan-TM-Poly/Tristan_Tardif-Morency_TFUG",
        "public",
        "Large TFUG corpus; current runtime adapter targets the existing protein_fold_tristan package",
        distribution="protein-fold-tristan",
        package_hint="protein_fold_tristan",
        packaging_status="adapter-candidate",
        notes="Protein adapter exposes bounded dependency-free computational primitives and was executed inside the verified four-repository matrix.",
        adapter_branch="feat/tristan-runtime-adapter-r01",
        adapter_commit="42c3467b2675c7d83beae6b274586dc2cdf77d42",
        runtime_capabilities=(
            "protein-fold-tristan.sequence-validate",
            "protein-fold-tristan.contact-map",
            "protein-fold-tristan.oak-level",
        ),
    ),
    RepositorySpec(
        "tfugag",
        "Tristan-TM-Poly/Tristan_Tardif-Morency_TFUGAG",
        "public",
        "TFUGAG companion repository",
        packaging_status="needs-packaging",
        notes="No root Python distribution has yet been promoted into the shared runtime contract.",
    ),
    RepositorySpec(
        "omni-core",
        "Tristan-TM-Poly/TTM-TFUGA-AI7-TRISTAN2",
        "public",
        "OAK-governed omni-core monorepo",
        distribution="tristan-omni-core",
        package_hint="tristan_omni_core",
        packaging_status="adapter-candidate",
        notes="Exact adapter commit was built, installed and executed in both three- and four-repository matrices; merge remains review-gated.",
        adapter_branch="feat/tristan-runtime-adapter-r01",
        adapter_commit="29e77ad2e1214eb536043b31670071f5079285a5",
        runtime_capabilities=("tristan-omni-core.evidence-to-idea", "tristan-omni-core.valuation-assess"),
    ),
)


class RepoRegistry:
    _SCORES = {"package": 1.0, "adapter-candidate": 0.85, "partial": 0.55, "needs-packaging": 0.2, "unknown": 0.0}

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
            actions.append("Keep adapter exact-pinned and review-gated; CI integration does not authorize default-branch merge.")
        elif repo.packaging_status != "package":
            actions.append("Generate/review a root distribution and bounded tristan.plugins adapter.")
        if repo.distribution and not installed:
            actions.append(f"Build/install an exact-pinned wheel for {repo.distribution}.")
        if repo.runtime_capabilities:
            actions.append("Retain capability tests, provenance, immutable source pins and OAK interpretation boundaries.")
        else:
            actions.append("Publish no runtime capability until a real kernel and dependency boundary are identified.")
        return tuple(actions)

    def doctor(self) -> tuple[RepositoryHealth, ...]:
        checks: list[RepositoryHealth] = []
        for repo in self._repositories:
            score = self._SCORES.get(repo.packaging_status, 0.0)
            if not repo.distribution:
                checks.append(RepositoryHealth(repo.key, repo.full_name, "needs-packaging", None, None, repo.packaging_status, score, "No installable root distribution is registered yet.", self._actions(repo, False)))
                continue
            try:
                version = metadata.version(repo.distribution)
            except metadata.PackageNotFoundError:
                checks.append(RepositoryHealth(repo.key, repo.full_name, "not-installed", repo.distribution, None, repo.packaging_status, score, f"Python distribution {repo.distribution!r} is not installed in this interpreter.", self._actions(repo, False)))
            else:
                checks.append(RepositoryHealth(repo.key, repo.full_name, "installed", repo.distribution, version, repo.packaging_status, score, "Distribution metadata is available in the active Python environment.", self._actions(repo, True)))
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
            "verified_environment": "CI_VERIFIED_FOUR_REPO_R02",
            "oak_rule": "Packaging and multi-repository CI are software evidence, not scientific truth or merge authorization.",
        }
