from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, Mapping, Tuple


@dataclass(frozen=True)
class PublicSourceSpec:
    """Registry entry for an external neuroscience source.

    A registry entry is not an endorsement of every asset exposed by the
    provider. Asset-level version, license, provenance and integrity review are
    still required before an observation can enter an evidence campaign.
    """

    source_id: str
    provider: str
    documentation_uri: str
    api_uri: str
    modalities: Tuple[str, ...]
    formats: Tuple[str, ...]
    candidate_hypotheses: Tuple[str, ...]
    version_strategy: str
    grouping_strategy: str
    license_strategy: str
    caveats: Tuple[str, ...]
    access_mode: str = "public"
    provenance_review_required: bool = True
    license_review_required: bool = True
    automatic_biological_promotion: bool = False

    def __post_init__(self) -> None:
        for name in (
            "source_id",
            "provider",
            "documentation_uri",
            "api_uri",
            "version_strategy",
            "grouping_strategy",
            "license_strategy",
        ):
            if not getattr(self, name):
                raise ValueError(f"{name} must be non-empty")
        if self.access_mode != "public":
            raise ValueError("R0.6 registry only admits public source classes")
        if not self.modalities or not self.formats or not self.candidate_hypotheses:
            raise ValueError("modalities, formats and candidate_hypotheses must be non-empty")
        if self.automatic_biological_promotion:
            raise ValueError("public data cannot automatically promote a biological claim")

    def to_dict(self) -> Mapping[str, object]:
        return asdict(self)


PUBLIC_SOURCES: Dict[str, PublicSourceSpec] = {
    "allen_cell_types": PublicSourceSpec(
        source_id="allen_cell_types",
        provider="Allen Institute for Brain Science",
        documentation_uri="https://brain-map.org/support/documentation/cell-types-database-api",
        api_uri="https://api.brain-map.org/api/v2",
        modalities=("intracellular_electrophysiology", "morphology", "single_cell_models"),
        formats=("NWB", "SWC", "JSON/XML metadata"),
        candidate_hypotheses=("P1_DENDRITIC_ADDRESS", "P2_SYNAPTIC_STATE_TENSOR", "P4_MORPHOLOGY_COMPUTATION"),
        version_strategy=(
            "record specimen_id plus returned well-known-file/model identifiers, retrieval timestamp, "
            "and sha256 of every downloaded payload"
        ),
        grouping_strategy="hold out specimen_id; donor-level holdout when combining human cells",
        license_strategy="review Allen source/citation terms and each downloaded asset before admission",
        caveats=(
            "not every specimen has a morphology reconstruction",
            "mouse and human specimens must not be pooled without explicit species/donor controls",
            "somatic current-injection recordings do not directly identify synapse-level causal state",
        ),
    ),
    "microns_mm3": PublicSourceSpec(
        source_id="microns_mm3",
        provider="MICrONS Consortium",
        documentation_uri="https://www.microns-explorer.org/cortical-mm3",
        api_uri="https://www.microns-explorer.org/manifests/mm3-v343",
        modalities=("electron_microscopy_connectomics", "two_photon_function", "cell_types", "coregistration"),
        formats=("CAVE tables", "cloud volumes", "tabular exports", "functional arrays"),
        candidate_hypotheses=("P3_HIGHER_ORDER_WIRING", "P5_DYNAMIC_CONNECTOME", "P7_GLIAL_HYPEREDGE"),
        version_strategy=(
            "freeze materialization/data-release identifier, table names, query text, returned root IDs, "
            "export hash and analysis commit"
        ),
        grouping_strategy=(
            "hold out neurons/cells at the unit required by the hypothesis; keep session/scan identity and "
            "coregistration provenance to prevent repeated-unit leakage"
        ),
        license_strategy="follow MICrONS citation/data-use policy and review the terms of each access path",
        caveats=(
            "the cubic-millimeter resource is centered on one mouse and cannot establish population universality",
            "automated and manually verified coregistration tables have different confidence levels",
            "segmentation/proofreading/materialization state can change and must be frozen",
        ),
    ),
    "dandi_nwb": PublicSourceSpec(
        source_id="dandi_nwb",
        provider="DANDI Archive",
        documentation_uri="https://docs.dandiarchive.org/introduction/",
        api_uri="https://api.dandiarchive.org/",
        modalities=("electrophysiology", "optophysiology", "behavior", "microscopy", "neuroimaging"),
        formats=("NWB", "BIDS", "OME-TIFF", "OME-Zarr"),
        candidate_hypotheses=(
            "P1_DENDRITIC_ADDRESS",
            "P2_SYNAPTIC_STATE_TENSOR",
            "P5_DYNAMIC_CONNECTOME",
            "P6_MULTISCALE_NEUROCODE",
        ),
        version_strategy="freeze dandiset_id, published version, asset_id/contentUrl and asset sha256",
        grouping_strategy="derive subject/session/experiment group keys from standardized metadata before splitting",
        license_strategy="license is dandiset-specific; record and review it at asset admission time",
        caveats=(
            "DANDI is an archive, not one homogeneous experiment",
            "candidate hypotheses require dandiset-specific variable mapping and controls",
            "draft dandisets are mutable; prefer published immutable versions for evidence claims",
        ),
    ),
}


def get_public_source(source_id: str) -> PublicSourceSpec:
    try:
        return PUBLIC_SOURCES[source_id]
    except KeyError as exc:
        raise KeyError(f"unknown public neuroscience source: {source_id}") from exc


def public_source_registry() -> Mapping[str, Mapping[str, object]]:
    return {source_id: spec.to_dict() for source_id, spec in sorted(PUBLIC_SOURCES.items())}
