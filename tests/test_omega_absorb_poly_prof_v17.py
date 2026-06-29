from omega_prof_poly_t import (
    VERSION,
    answer_twin_question,
    build_department_strategy_matrix,
    build_poly_research_twin_v3,
    build_professor_tensors,
    build_route_confidence_dashboard,
    render_department_strategy_matrix,
    render_route_confidence_dashboard,
    render_tensor_weights_table,
    render_twin_answer,
    run_cli,
    select_demo_records,
    weight_professor_tensors,
)
from omega_prof_poly_t.absorb_public_research import absorb_public_records
from omega_prof_poly_t.professor_genome import build_all_professor_genomes


def _tensors():
    atoms = absorb_public_records(select_demo_records("combined")).atoms
    genomes = build_all_professor_genomes(atoms)
    return build_professor_tensors(genomes)


def test_v17_cli_commands():
    assert VERSION == "1.7.0"
    assert run_cli(["version"]) == "omega-absorb 1.7.0\n"
    assert run_cli(["tensor-weights", "--source", "combined"]).startswith("professor | teaching")
    assert run_cli(["twin-answer", "--source", "combined", "--question", "next-10"]).startswith("# Twin answer")
    assert run_cli(["department-matrix", "--source", "combined"]).startswith("department | teaching")
    assert run_cli(["route-dashboard", "--source", "combined"]).startswith("index | source")


def test_weighted_professor_tensors():
    weights = weight_professor_tensors(_tensors())
    assert weights
    assert 0 <= weights[0].teaching <= 1
    assert render_tensor_weights_table(weights).startswith("professor | teaching")


def test_poly_research_twin_v3_answers():
    twin = build_poly_research_twin_v3(select_demo_records("combined"))
    assert twin.weights
    answer = answer_twin_question(twin, "weighted-routes")
    assert answer.answers
    assert render_twin_answer(answer).startswith("# Twin answer")


def test_department_strategy_matrix():
    matrix = build_department_strategy_matrix(_tensors())
    assert matrix.cells
    assert render_department_strategy_matrix(matrix).startswith("department | teaching")


def test_route_confidence_dashboard():
    dashboard = build_route_confidence_dashboard(select_demo_records("combined"))
    assert dashboard.rows
    assert dashboard.average_confidence > 0
    assert render_route_confidence_dashboard(dashboard).startswith("index | source")
