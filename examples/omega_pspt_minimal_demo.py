"""Minimal Omega-PSPT++ demo.

Run from repository root:

    python examples/omega_pspt_minimal_demo.py

This demo is deliberately small and dependency-free. It prints OAK-2 style
geometry, transport, and spectral descriptors for a Sierpinski support.
"""

from sage_tristan.omega_pspt import OMEGA_TFTS
from sage_tristan.omega_pspt_geometry import nearest_neighbor_edges, sierpinski_carpet_points, summarize_graph
from sage_tristan.omega_pspt_spectral import cvcd_spectral_features, spectral_summary
from sage_tristan.omega_pspt_transport import normalized_conductance_score, summarize_transport


def main() -> None:
    iteration = 1
    points = sierpinski_carpet_points(iteration)
    edges = nearest_neighbor_edges(points)
    graph = summarize_graph(points)
    transport = summarize_transport(points, edges, axis=0)
    spectral = spectral_summary(edges)
    features = cvcd_spectral_features(spectral)
    bounding_area = (3**iteration) ** 2
    normalized_g = normalized_conductance_score(transport, len(points), bounding_area)

    print("Omega-PSPT++ minimal demo")
    print("==========================")
    print(f"geometry: sierpinski_carpet")
    print(f"iteration: {iteration}")
    print(f"sites: {len(points)}")
    print(f"edges: {len(edges)}")
    print(f"cycle_rank beta_1: {graph.cycle_rank}")
    print(f"effective_resistance: {transport.effective_resistance:.6f}")
    print(f"effective_conductance: {transport.effective_conductance:.6f}")
    print(f"normalized_conductance_score: {normalized_g:.6f}")
    print(f"trace_A2: {spectral.trace_a2:.1f}")
    print(f"trace_A4: {spectral.trace_a4:.1f}")
    print(f"cvcd_spectral_features: {features}")
    print(f"Omega-TFTS claim allowed at current level: {OMEGA_TFTS.is_claim_allowed()}")
    print(f"Missing for OAK-6: {OMEGA_TFTS.missing_for_promotion('OAK_6')}")


if __name__ == "__main__":
    main()
