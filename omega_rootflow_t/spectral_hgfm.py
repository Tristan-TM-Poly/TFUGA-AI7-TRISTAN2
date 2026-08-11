"""Compile ROOTFLOW trajectories into an auditable spectral hypergraph.

The graph is intentionally lightweight and JSON-native.  It provides the
interoperability layer needed to hand ROOTFLOW trajectories to HGFM/CVCD/OAK
without introducing a graph database dependency inside the numerical kernel.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from .projective import chordal_distance
from .projective_flow import ProjectiveFlowResult, track_projective_path


@dataclass(frozen=True)
class SpectralHGFM:
    nodes: tuple[dict[str, object], ...]
    edges: tuple[dict[str, object], ...]
    hyperedges: tuple[dict[str, object], ...]
    invariants: dict[str, object]
    status: str
    theorem_claimed: bool = False
    scientific_validation_claimed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "omega-rootflow-spectral-hgfm-r0.4",
            "nodes": list(self.nodes),
            "edges": list(self.edges),
            "hyperedges": list(self.hyperedges),
            "invariants": dict(self.invariants),
            "status": self.status,
            "theorem_claimed": self.theorem_claimed,
            "scientific_validation_claimed": self.scientific_validation_claimed,
        }


def compile_projective_flow_hgfm(flow: ProjectiveFlowResult) -> SpectralHGFM:
    """Compile an ordered projective flow into nodes, edges and spectrum fibers."""
    if not flow.steps:
        raise ValueError("flow must contain at least one step")
    root_count = len(flow.steps[0].roots)
    if any(len(step.roots) != root_count for step in flow.steps):
        raise ValueError("projective flow changed nominal root cardinality")

    nodes: list[dict[str, object]] = []
    edges: list[dict[str, object]] = []
    hyperedges: list[dict[str, object]] = []
    infinity_events = 0
    maximum_branch_distance = 0.0

    for sample_index, step in enumerate(flow.steps):
        coefficient_id = f"c:{sample_index}"
        nodes.append(
            {
                "id": coefficient_id,
                "kind": "coefficient_state",
                "parameter": step.parameter,
                "coefficients": [[float(z.real), float(z.imag)] for z in step.coefficients],
                "infinity_multiplicity": step.infinity_multiplicity,
            }
        )
        members = [coefficient_id]
        for branch_index, root in enumerate(step.roots):
            root_id = f"r:{sample_index}:{branch_index}"
            members.append(root_id)
            affine = root.affine
            nodes.append(
                {
                    "id": root_id,
                    "kind": "projective_root",
                    "sample": sample_index,
                    "branch": branch_index,
                    "u": [float(root.u.real), float(root.u.imag)],
                    "v": [float(root.v.real), float(root.v.imag)],
                    "at_infinity": root.at_infinity,
                    "affine": None
                    if affine is None
                    else [float(affine.real), float(affine.imag)],
                }
            )
        hyperedges.append(
            {
                "id": f"fiber:{sample_index}",
                "kind": "spectrum_fiber",
                "members": members,
                "nominal_root_count": root_count,
            }
        )

        if sample_index > 0:
            previous = flow.steps[sample_index - 1]
            edges.append(
                {
                    "id": f"coeff-flow:{sample_index-1}:{sample_index}",
                    "kind": "coefficient_flow",
                    "source": f"c:{sample_index-1}",
                    "target": coefficient_id,
                    "parameter_delta": step.parameter - previous.parameter,
                }
            )
            if step.infinity_multiplicity != previous.infinity_multiplicity:
                infinity_events += 1
            for branch_index, root in enumerate(step.roots):
                previous_root = previous.roots[branch_index]
                distance = chordal_distance(previous_root, root)
                maximum_branch_distance = max(maximum_branch_distance, distance)
                edges.append(
                    {
                        "id": f"branch:{branch_index}:{sample_index-1}:{sample_index}",
                        "kind": "root_branch_flow",
                        "source": f"r:{sample_index-1}:{branch_index}",
                        "target": f"r:{sample_index}:{branch_index}",
                        "branch": branch_index,
                        "chordal_distance": distance,
                        "entered_or_left_infinity": previous_root.at_infinity != root.at_infinity,
                    }
                )

    invariants: dict[str, object] = {
        "sample_count": len(flow.steps),
        "nominal_root_count": root_count,
        "constant_fiber_cardinality": True,
        "degree_transition_count": flow.degree_transition_count,
        "infinity_transition_edges": infinity_events,
        "maximum_branch_chordal_distance": maximum_branch_distance,
        "source_flow_status": flow.status,
    }
    return SpectralHGFM(
        nodes=tuple(nodes),
        edges=tuple(edges),
        hyperedges=tuple(hyperedges),
        invariants=invariants,
        status="OAK_PASS_SPECTRAL_HGFM_COMPILE",
    )


def build_spectral_hgfm(
    coefficient_path: npt.ArrayLike,
    *,
    coefficient_tolerance: float = 0.0,
) -> SpectralHGFM:
    """Convenience compiler from coefficient samples directly to HGFM payload."""
    path = np.asarray(coefficient_path, dtype=np.complex128)
    flow = track_projective_path(path, coefficient_tolerance=coefficient_tolerance)
    return compile_projective_flow_hgfm(flow)
