from omega_prof_poly_t import (
    VERSION,
    build_all_professor_genomes,
    build_oak_packet_manifest,
    build_poly_research_twin_v2,
    build_professor_tensors,
    compile_top_next_actions,
    optimize_department_bridges,
    recommend_collaborations,
    render_next_actions_markdown,
    run_cli,
    select_demo_records,
)
from omega_prof_poly_t.absorb_public_research import absorb_public_records


def test_v15_cli_commands():
    assert VERSION == "1.5.0"
    assert run_cli(["version"]) == "omega-absorb 1.5.0\n"
    assert run_cli(["tensor", "--source", "combined"]).startswith("professor_tensors=")
    assert run_cli(["twin-v2", "--source", "combined"]).startswith("twin_tensors=")
    assert run_cli(["bridge-opt", "--source", "combined"]).startswith("optimized_bridges=")


def test_professor_tensors_from_genomes():
    atoms = absorb_public_records(select_demo_records("combined")).atoms
    genomes = build_all_professor_genomes(atoms)
    tensors = build_professor_tensors(genomes)
    assert tensors
    assert tensors[0].professor
    assert tensors[0].next_action == "rank_professor_routes"


def test_twin_v2_and_next_actions():
    twin = build_poly_research_twin_v2(select_demo_records("combined"))
    assert twin.tensors
    assert twin.bridge_score > 0
    plan = compile_top_next_actions(twin)
    assert plan.actions
    assert render_next_actions_markdown(plan).startswith("# Omega Absorb Top Next Actions")


def test_bridge_optimizer_and_oak_manifest():
    atoms = absorb_public_records(select_demo_records("combined")).atoms
    genomes = build_all_professor_genomes(atoms)
    recs = recommend_collaborations(genomes).recommendations
    bridges = optimize_department_bridges(recs)
    assert bridges.next_action == "route_top_bridges_to_action_engine"
    twin = build_poly_research_twin_v2(select_demo_records("combined"))
    actions = compile_top_next_actions(twin, bridges.bridges)
    manifest = build_oak_packet_manifest(actions.actions)
    assert manifest.entries
    assert "oak-" in manifest.entries[0].packet_id
    assert "entries" in manifest.manifest_json


def test_new_cli_outputs():
    assert run_cli(["next-actions", "--source", "combined"]).startswith("# Omega Absorb Top Next Actions")
    assert "entries" in run_cli(["oak-manifest", "--source", "combined"])
