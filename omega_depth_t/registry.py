from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .model import CodeStatus, IpStatus, NodeContract, OakStatus, RiskLevel


@dataclass(frozen=True, slots=True)
class CreationRoot:
    index: int
    slug: str
    name: str
    category: str
    status: OakStatus = OakStatus.FERTILE

    @property
    def node_id(self) -> str:
        return self.slug.replace("-", "_")

    def to_node(self) -> NodeContract:
        return NodeContract(
            id=self.node_id,
            name=self.name,
            depth=0,
            path=self.slug,
            parent_id=None,
            root_creation=self.name,
            role=f"Racine récursive de {self.name}.",
            oak_status=self.status,
            code_status=CodeStatus.ABSENT,
            ip_status=IpStatus.REVIEW_REQUIRED,
            risk_level=RiskLevel.LOW,
            next_proof="Décomposer la racine en systèmes n=1 avec interfaces et preuves attendues.",
            next_action_under_2h="Créer et valider le premier manifeste de profondeur n=1.",
            tags=("tristan-creation", self.category, "depth-root"),
            metadata={"atomic": False, "registry_index": self.index},
        )


CREATION_ROOTS: tuple[CreationRoot, ...] = (
    CreationRoot(1, "hgfm", "HGFM — Hypergraphes Fractals Mycéliens", "core", OakStatus.CODED),
    CreationRoot(2, "log", "LOG — Compression structurée", "core"),
    CreationRoot(3, "cvcd", "CVCD — Invariants fertiles", "core"),
    CreationRoot(4, "exp", "EXP — Décompression générative", "core"),
    CreationRoot(5, "oak", "OAK — Validation et falsification", "core", OakStatus.CODED),
    CreationRoot(6, "m-plus-m-minus", "M⁺ / M⁻ — Mémoire positive et négative", "core", OakStatus.CODED),
    CreationRoot(7, "omega-unc2-t", "Ω-UNC²-T — Incertitude de l’incertitude", "core"),
    CreationRoot(8, "omega-sans-plafond-t", "Ω-SANS-PLAFOND-T∞", "core", OakStatus.TESTED),
    CreationRoot(9, "sage-tristan", "SAGE-Tristan", "ai"),
    CreationRoot(10, "ai7-ait-pantheon", "AI-7 / AIT-PANTHEON", "ai"),
    CreationRoot(11, "omega-doc-t", "Ω-DOC-T — Documentation vivante", "knowledge"),
    CreationRoot(12, "omega-rosette-t", "Ω-ROSETTE-T", "knowledge"),
    CreationRoot(13, "omega-pdf-hypergraph-github-t", "Ω-PDF-HYPERGRAPH-GITHUB-T", "knowledge", OakStatus.CODED),
    CreationRoot(14, "omega-web-hg-t", "Ω-WEB-HG-T∞", "knowledge", OakStatus.CODED),
    CreationRoot(15, "wikiforge-t", "WikiForge-T / Ω-WIKI-T∞", "knowledge", OakStatus.TESTED),
    CreationRoot(16, "omega-oss-digest-t", "Ω-OSS-DIGEST-T", "knowledge"),
    CreationRoot(17, "omega-gdm-t", "Ω-GDM-T", "knowledge"),
    CreationRoot(18, "omega-transform-t", "Ω-TRANSFORM-T", "mathematics", OakStatus.CODED),
    CreationRoot(19, "ffwt", "FFWT — Fast Fractal Wavelet Transform", "mathematics", OakStatus.TESTED),
    CreationRoot(20, "ffwt-hac-cvcd", "FFWT-HAC-CVCD", "mathematics"),
    CreationRoot(21, "omega-zeta-mandel-t", "Ω-ZETA-MANDEL-T", "mathematics"),
    CreationRoot(22, "omega-logexp-morph-t", "Ω-LOGEXP-MORPH-T∞²", "mathematics", OakStatus.TESTED),
    CreationRoot(23, "omega-fcryst-t", "Ω-FCRYST-T — Cristaux fractals", "matter"),
    CreationRoot(24, "omega-org-fam-t", "Ω-ORG-FAM-T", "matter", OakStatus.CODED),
    CreationRoot(25, "omega-oemmtd-t", "Ω-OEMMTD-T", "matter"),
    CreationRoot(26, "omega-3dp-t", "Ω-3DP-T — Fabrication additive", "matter"),
    CreationRoot(27, "omega-protein-fold-t", "Ω-PROTEIN-FOLD-T", "matter"),
    CreationRoot(28, "omega-circuits-t", "Ω-CIRCUITS-T", "physics"),
    CreationRoot(29, "omega-energy-t", "Ω-ENERGY-T", "physics"),
    CreationRoot(30, "omega-emr-source-t", "Ω-EMR-SOURCE-T∞", "physics"),
    CreationRoot(31, "omega-space-systems-t", "Ω-SPACE-SYSTEMS-T∞", "physics"),
    CreationRoot(32, "omega-natsci-t", "Ω-NATSCI-T", "science"),
    CreationRoot(33, "omega-re-t", "Ω-RE-T∞", "engineering", OakStatus.TESTED),
    CreationRoot(34, "omega-auto2-t", "Ω-AUTO²-T", "engineering"),
    CreationRoot(35, "oakgate-github-factory", "OAKGate GitHub Factory", "engineering"),
    CreationRoot(36, "omega-rev-t", "Ω-REV-T — Revenus", "business"),
    CreationRoot(37, "asset-ip-revenue-classifier", "Tristan Asset/IP/Revenue Classifier", "business"),
    CreationRoot(38, "omega-prof-poly-t", "Ω-PROF-POLY-T", "institution"),
    CreationRoot(39, "omega-neg-t", "Ω-NEG-T — Néguentropie", "cognition"),
    CreationRoot(40, "omega-jkd-t", "Ω-JKD-T — Jeet Kun de Tristan", "cognition"),
)


def creation_roots() -> tuple[CreationRoot, ...]:
    return CREATION_ROOTS


def find_root(slug_or_id: str) -> CreationRoot:
    normalized = slug_or_id.replace("_", "-").lower()
    for root in CREATION_ROOTS:
        if root.slug == normalized or root.node_id == slug_or_id:
            return root
    raise KeyError(f"unknown creation root: {slug_or_id}")


def root_nodes(roots: Iterable[CreationRoot] = CREATION_ROOTS) -> tuple[NodeContract, ...]:
    return tuple(root.to_node() for root in roots)
