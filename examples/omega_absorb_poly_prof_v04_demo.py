from omega_prof_poly_t import (
    absorb_public_records,
    build_claim_graph,
    build_method_graph,
    compile_research_opportunities,
    demo_public_research_records,
    packet_digest,
    render_packet_report,
    to_deterministic_json,
)


def main() -> None:
    absorption = absorb_public_records(demo_public_research_records())
    claim_graph = build_claim_graph(absorption.atoms)
    method_graph = build_method_graph(absorption.atoms)
    opportunities = compile_research_opportunities(absorption.atoms)
    print(render_packet_report("Ω-ABSORB-POLY-PROF-T v0.4 demo", (absorption, claim_graph, method_graph, opportunities)))
    print("digest", packet_digest(opportunities))
    print(to_deterministic_json({"claim_count": len(claim_graph.claims), "method_count": len(method_graph.methods)}))


if __name__ == "__main__":
    main()
