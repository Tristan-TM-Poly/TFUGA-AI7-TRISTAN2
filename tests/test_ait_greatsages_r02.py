from sage_tristan.greatsages import ClaimClass, MirrorKind, get_profile
from sage_tristan.greatsages_bench import (
    BenchmarkTask,
    audit_case,
    build_benchmark_case,
    build_suite,
    compile_bench_report,
    learning_compiler,
    meta_sage_plan,
    route_operators,
    white_space_atlas,
)
from sage_tristan.greatsages_time_machine import (
    Admissibility,
    KnowledgeLayer,
    TemporalAxis,
    TemporalVector,
    causal_leakage_firewall,
    compile_operator_program,
    compose_mirrors,
    default_context,
    digital_twin,
    discovery_descendants,
    epistemic_debt_for_discovery,
    estimate_discovery_potential,
    genome_distance,
    genome_from_discovery,
    instrument_admissibility,
    knowledge_field,
    lineage_receipt,
    minimal_discovery_set,
    notation_admissibility,
    operator_registry,
    structural_transfer_candidates,
    time_machine_snapshot,
)


GAUSS = get_profile("gauss")


def test_temporal_vector_does_not_infer_private_axes_from_publication():
    vector = TemporalVector(world=1796, published=1801)
    assert vector.effective_year(TemporalAxis.ACCESSIBLE) == 1796
    assert vector.effective_year(TemporalAxis.READ) is None
    assert vector.effective_year(TemporalAxis.UNDERSTOOD) is None


def test_time_machine_separates_layers_and_future_knowledge():
    context = default_context(GAUSS, 1795)
    snapshot = time_machine_snapshot(GAUSS, context)
    assert snapshot.leakage_free is True
    assert "cyclotomy_seed" in snapshot.blocked_atom_ids
    assert "gauss_latent_invariant_operator" in snapshot.blocked_by_layer_atom_ids
    assert "gauss_2026_counterfactual_tooling" in snapshot.blocked_by_layer_atom_ids
    assert "modern_linear_algebra" not in context.notation_ids
    assert "modern_computer" not in context.instrument_ids


def test_1801_context_admits_historically_seeded_capabilities_but_not_modern_tools():
    context = default_context(GAUSS, 1801)
    snapshot = time_machine_snapshot(GAUSS, context)
    assert "cyclotomy_seed" in snapshot.allowed_atom_ids
    assert "congruence_language" in snapshot.allowed_atom_ids
    assert "orbit_inference" in snapshot.allowed_atom_ids
    assert notation_admissibility(GAUSS, "gaussian_congruence_notation", 1801) is Admissibility.ALLOWED
    assert notation_admissibility(GAUSS, "modern_linear_algebra", 1801) is Admissibility.BLOCKED_NOTATION
    assert instrument_admissibility(GAUSS, "modern_computer", 1801) is Admissibility.BLOCKED_INSTRUMENT


def test_causal_firewall_masks_target_descendants_and_all_future_discoveries():
    firewall = causal_leakage_firewall(GAUSS, "gauss_1801_ceres")
    descendants = discovery_descendants(GAUSS, "gauss_1801_ceres")
    assert "gauss_1809_theoria_motus" in descendants
    assert firewall.target_masked is True
    assert "gauss_1801_ceres" in firewall.masked_discovery_ids
    assert "gauss_1809_theoria_motus" in firewall.masked_discovery_ids
    assert not (set(firewall.visible_discovery_ids) & set(firewall.masked_discovery_ids))


def test_mirror_algebra_propagates_epistemic_class():
    historical_oak = compose_mirrors(MirrorKind.OAK, MirrorKind.HISTORICAL)
    tristan_compute = compose_mirrors(MirrorKind.TRISTAN, MirrorKind.COMPUTATIONAL)
    future_tristan = compose_mirrors(MirrorKind.FUTURE, MirrorKind.TRISTAN, MirrorKind.COMPUTATIONAL)
    assert historical_oak.claim_class is ClaimClass.RECONSTRUCTION
    assert tristan_compute.claim_class is ClaimClass.FERTILE_HYPOTHESIS
    assert future_tristan.claim_class is ClaimClass.COUNTERFACTUAL
    assert "future" in future_tristan.expression


def test_discovery_genome_distance_is_deterministic_and_self_zero():
    ceres = genome_from_discovery(GAUSS, "gauss_1801_ceres")
    surfaces = genome_from_discovery(GAUSS, "gauss_1827_surfaces")
    assert genome_distance(ceres, ceres) == 0.0
    assert 0.0 <= genome_distance(ceres, surfaces) <= 1.0
    assert structural_transfer_candidates(GAUSS, "gauss_1801_ceres") == structural_transfer_candidates(GAUSS, "gauss_1801_ceres")


def test_minimal_discovery_set_is_transitive_prerequisite_closure():
    assert minimal_discovery_set(GAUSS, "gauss_1809_theoria_motus") == ("gauss_1801_ceres",)
    assert minimal_discovery_set(GAUSS, "gauss_1801_disquisitiones") == ("gauss_1796_17gon",)


def test_knowledge_field_partitions_current_finite_seed():
    field = knowledge_field(GAUSS, 1800)
    all_ids = set(field.known_ids) | set(field.frontier_ids) | set(field.unknown_ids)
    expected = {item.discovery_id for item in GAUSS.discoveries}
    assert all_ids == expected
    assert not (set(field.known_ids) & set(field.frontier_ids))
    assert not (set(field.known_ids) & set(field.unknown_ids))
    assert not (set(field.frontier_ids) & set(field.unknown_ids))


def test_discovery_potential_is_bounded_and_exposes_barrier():
    potential = estimate_discovery_potential(GAUSS, "gauss_1801_ceres", year=1800)
    assert 0.0 <= potential.accessibility <= 1.0
    assert 0.0 <= potential.discovery_barrier <= 1.0
    assert round(potential.accessibility + potential.discovery_barrier, 6) == 1.0


def test_operator_compiler_has_anti_operator_pairs_and_rejects_unknowns():
    registry = operator_registry(GAUSS)
    assert registry["invariant_search"].counter_operator_id == "anti_invariant_residual"
    program = compile_operator_program(GAUSS, ("representation_switch", "invariant_search"))
    assert program.assembly == "representation_switch -> invariant_search"
    try:
        compile_operator_program(GAUSS, ("does_not_exist",))
    except KeyError:
        pass
    else:
        raise AssertionError("unknown operator must fail")


def test_epistemic_debt_and_lineage_hash_are_explicit_and_deterministic():
    debt = epistemic_debt_for_discovery(GAUSS, "gauss_1801_ceres")
    mirror = compose_mirrors(MirrorKind.OAK, MirrorKind.TRISTAN)
    receipt_a = lineage_receipt(GAUSS, "gauss_1801_ceres", mirror=mirror, operator_ids=("representation_switch",))
    receipt_b = lineage_receipt(GAUSS, "gauss_1801_ceres", mirror=mirror, operator_ids=("representation_switch",))
    assert debt.score > 0
    assert receipt_a.lineage_hash == receipt_b.lineage_hash
    assert len(receipt_a.lineage_hash) == 64
    assert receipt_a.claim_class is ClaimClass.FERTILE_HYPOTHESIS


def test_digital_twin_is_explicitly_model_not_person():
    twin = digital_twin(GAUSS, 1801)
    assert twin.model_not_person is True
    assert twin.knowledge_snapshot.leakage_free is True
    assert twin.uncertainty_notes


def test_benchmark_suite_covers_eight_task_families_and_promotes_software_gates_only():
    suite = build_suite(GAUSS, "gauss_1801_ceres")
    assert len(suite) == len(BenchmarkTask) == 8
    receipts = tuple(audit_case(GAUSS, case) for case in suite)
    assert all(receipt.leakage_free for receipt in receipts)
    assert all(receipt.target_withheld for receipt in receipts)
    assert all(receipt.status == "PROMOTE_SOFTWARE_BENCH" for receipt in receipts)


def test_learning_compiler_and_meta_sage_are_bounded_by_oak_contracts():
    path = learning_compiler(GAUSS, "gauss_1809_theoria_motus")
    assert "gauss_1801_ceres" in path.prerequisite_discovery_ids
    routed = route_operators(GAUSS, ("inverse", "astronomy"), top_k=3)
    assert len(routed) == 3
    plan = meta_sage_plan(GAUSS, ("inverse", "astronomy"), top_k=3)
    assert plan.selected_operator_ids
    assert plan.stop_conditions
    assert "do not promote novelty without external literature audit" in plan.oak_requirements


def test_white_space_atlas_marks_empty_cells_as_prompts_not_novelty():
    cells = white_space_atlas(GAUSS)
    assert cells
    assert any(cell.status == "WHITE_SPACE_CANDIDATE" for cell in cells)
    assert all(cell.observed_count >= 0 for cell in cells)


def test_compiled_bench_report_preserves_oak_boundaries():
    report = compile_bench_report(GAUSS, "gauss_1801_ceres")
    assert report["release"] == "R0.2"
    assert report["all_cases_promotable"] is True
    assert report["historical_truth_certified"] is False
    assert report["novelty_claimed_for_white_space"] is False
