from __future__ import annotations

from dataclasses import replace
import json
import math
from pathlib import Path

import pytest

from omega_solids_t.atlas import ARCHETYPE_NAMES, build_archetype, iter_archetypes
from omega_solids_t.calibration import (
    CalibrationPoint,
    compare_instruments,
    fit_linear_calibration,
)
from omega_solids_t.defects import DefectInteractionGraph, infer_pair_interaction
from omega_solids_t.energy import (
    EnergyFunctional,
    information_penalty_term,
    quadratic_elastic_term,
    surface_energy_term,
)
from omega_solids_t.genome import SolidGenome, load_genome, save_genome
from omega_solids_t.hypergraph import SolidHyperEdge, SolidHyperGraph, SolidNode
from omega_solids_t.invariants import (
    anisotropy_index_from_tensor,
    build_signature,
    compare_properties,
    normalized_entropy,
    signature_distance,
)
from omega_solids_t.inverse_design import (
    PropertyObjective,
    SolidCompiler,
    allowed_families,
    maximum_porosity,
    require_process_step,
)
from omega_solids_t.mechanics import (
    IsotropicElasticity,
    fracture_safety_factor,
    gibson_ashby_modulus,
    hall_petch_strength,
    rule_of_mixtures,
    thermal_strain,
    von_mises_stress,
)
from omega_solids_t.models import (
    BondClass,
    BondContribution,
    CompositionComponent,
    DefectKind,
    DefectRecord,
    EpistemicStatus,
    GateStatus,
    OrderClass,
    PhaseRecord,
    PropertyDomain,
    PropertyRecord,
    Quantity,
)
from omega_solids_t.oak import run_oak_gate
from omega_solids_t.ontology import classify, index_by_tag
from omega_solids_t.phases import PhaseGraph, PhaseTransition
from omega_solids_t.pipeline import SolidPipeline
from omega_solids_t.uncertainty import (
    Interval,
    combine_independent_standard_uncertainties,
    monte_carlo,
    normal_sampler,
    quantile,
    sensitivity_finite_difference,
    uniform_sampler,
)
from omega_solids_t.unbounded import (
    AdaptiveSolidFrontier,
    ArchetypeMutationSource,
    FrontierPolicy,
    JSONLGenomeSink,
)


def test_twelve_archetypes_are_available() -> None:
    assert len(ARCHETYPE_NAMES) == 12
    assert len(tuple(iter_archetypes())) == 12
    assert len({genome.identifier for genome in iter_archetypes()}) == 12


@pytest.mark.parametrize("name", ARCHETYPE_NAMES)
def test_archetype_round_trip(name: str, tmp_path: Path) -> None:
    genome = build_archetype(name)
    path = save_genome(genome, tmp_path / f"{name}.json")
    restored = load_genome(path)
    assert restored.to_dict() == genome.to_dict()
    assert restored.fingerprint() == genome.fingerprint()


@pytest.mark.parametrize("name", ARCHETYPE_NAMES)
def test_archetype_fractions_and_units(name: str) -> None:
    genome = build_archetype(name)
    assert sum(component.fraction for component in genome.composition) == pytest.approx(1.0)
    assert sum(bond.weight for bond in genome.bonds) == pytest.approx(1.0)
    assert sum(phase.fraction for phase in genome.phases) == pytest.approx(1.0)
    assert all(record.quantity.unit for record in genome.properties)


def test_invalid_composition_fraction_is_rejected() -> None:
    with pytest.raises(ValueError, match="Composition fractions"):
        SolidGenome(
            identifier="bad",
            name="bad",
            family="bad",
            composition=(CompositionComponent("A", 0.2),),
            bonds=(BondContribution(BondClass.COVALENT, 1.0),),
            order=OrderClass.UNKNOWN,
        )


def test_duplicate_property_name_is_rejected() -> None:
    property_record = PropertyRecord(
        "density",
        PropertyDomain.GEOMETRIC,
        Quantity(1000, "kg/m^3"),
    )
    with pytest.raises(ValueError, match="Property names"):
        SolidGenome(
            identifier="duplicate-property",
            name="duplicate",
            family="test",
            composition=(CompositionComponent("A", 1.0),),
            bonds=(BondContribution(BondClass.COVALENT, 1.0),),
            order=OrderClass.UNKNOWN,
            properties=(property_record, property_record),
        )


def test_fingerprint_ignores_only_creation_time() -> None:
    genome = build_archetype("metallic_crystal")
    changed_time = replace(genome, created_at="2000-01-01T00:00:00+00:00")
    changed_geometry = replace(genome, geometry={**genome.geometry, "grain_size_m": 1e-6})
    assert genome.fingerprint() == changed_time.fingerprint()
    assert genome.fingerprint() != changed_geometry.fingerprint()


def test_hypergraph_from_genome_is_connected_and_valid() -> None:
    for genome in iter_archetypes():
        graph = SolidHyperGraph.from_genome(genome)
        assert graph.validate() == ()
        assert len(graph.connected_components()) == 1
        assert len(graph.nodes) >= 1 + len(genome.composition) + len(genome.properties)
        assert len(graph.edges) >= 1


def test_hypergraph_rejects_missing_member() -> None:
    graph = SolidHyperGraph()
    graph.add_node(SolidNode("a", "kind", "A", "scale"))
    with pytest.raises(KeyError, match="missing nodes"):
        graph.add_edge(SolidHyperEdge("bad", "couples", ("a", "b")))


def test_hypergraph_shortest_path_and_graphml() -> None:
    graph = SolidHyperGraph()
    for value in "abcd":
        graph.add_node(SolidNode(value, "test", value.upper(), "unit"))
    graph.add_edge(SolidHyperEdge("e1", "couples", ("a", "b", "c")))
    graph.add_edge(SolidHyperEdge("e2", "couples", ("c", "d")))
    assert graph.shortest_hyperpath("a", "d") == ("a", "c", "d")
    graphml = graph.to_graphml()
    assert "hyperedge::e1" in graphml
    assert "inc::e2::1" in graphml


def test_cvcd_signatures_are_bounded_and_distinct() -> None:
    metal = build_signature(build_archetype("metallic_crystal"))
    porous = build_signature(build_archetype("porous_ceramic"))
    assert 0 <= metal.composition_entropy <= 1
    assert 0 <= porous.porosity < 1
    assert signature_distance(metal, metal) == pytest.approx(0.0)
    assert signature_distance(metal, porous) > 0


def test_normalized_entropy() -> None:
    assert normalized_entropy([1.0]) == 0.0
    assert normalized_entropy([0.5, 0.5]) == pytest.approx(1.0)
    assert normalized_entropy([0.9, 0.1]) < 1.0


def test_tensor_anisotropy() -> None:
    isotropic = ((10.0, 0.0, 0.0), (0.0, 10.0, 0.0), (0.0, 0.0, 10.0))
    orthotropic = ((100.0, 0.0, 0.0), (0.0, 10.0, 0.0), (0.0, 0.0, 5.0))
    assert anisotropy_index_from_tensor(isotropic) == pytest.approx(0.0)
    assert anisotropy_index_from_tensor(orthotropic) > 1.0


def test_property_comparison_detects_units() -> None:
    metal = build_archetype("metallic_crystal")
    modified = replace(
        metal,
        properties=tuple(
            replace(record, quantity=replace(record.quantity, unit="GPa"))
            if record.name == "young_modulus"
            else record
            for record in metal.properties
        ),
    )
    comparison = compare_properties(metal, modified)
    assert comparison["young_modulus"]["status"] == "unit_mismatch"


def test_defect_interaction_inference() -> None:
    crack = DefectRecord(DefectKind.CRACK, criticality=0.8)
    pore = DefectRecord(DefectKind.PORE, criticality=0.6)
    mechanism, strength = infer_pair_interaction(crack, pore)
    assert mechanism == "stress_concentration_coalescence"
    assert 0 < strength <= 1


def test_defect_tensor_and_cascade() -> None:
    genome = build_archetype("fiber_composite")
    graph = DefectInteractionGraph.infer(genome)
    tensor = graph.tensor()
    assert tensor.maximum_criticality == pytest.approx(0.75)
    assert 0 <= tensor.interaction_density <= 1
    assert 0 <= tensor.cascade_risk <= 1


def test_phase_graph_minimum_path() -> None:
    phases = (
        PhaseRecord("a", 1.0, OrderClass.PERIODIC_CRYSTAL),
        PhaseRecord("b", 0.0, OrderClass.PERIODIC_CRYSTAL),
        PhaseRecord("c", 0.0, OrderClass.PERIODIC_CRYSTAL),
    )
    graph = PhaseGraph(phases)
    graph.add_transition(PhaseTransition("a", "b", 10.0))
    graph.add_transition(PhaseTransition("b", "c", 10.0))
    graph.add_transition(PhaseTransition("a", "c", 25.0))
    path, cost = graph.minimum_barrier_path("a", "c") or ((), math.inf)
    assert path == ("a", "b", "c")
    assert cost == pytest.approx(20.0)


def test_phase_arrhenius_factor() -> None:
    transition = PhaseTransition("a", "b", 5000.0)
    factor_low = transition.arrhenius_factor(300)
    factor_high = transition.arrhenius_factor(600)
    assert 0 < factor_low < factor_high < 1


def test_isotropic_elasticity_relations() -> None:
    model = IsotropicElasticity(200e9, 0.3)
    assert model.shear_pa == pytest.approx(200e9 / 2.6)
    assert model.bulk_pa == pytest.approx(200e9 / 1.2)
    stress = model.stress((1e-3, 0, 0, 0, 0, 0))
    assert stress[0] > stress[1] > 0


def test_mixture_bounds() -> None:
    values = (200e9, 3e9)
    fractions = (0.6, 0.4)
    voigt = rule_of_mixtures(values, fractions, mode="voigt")
    reuss = rule_of_mixtures(values, fractions, mode="reuss")
    hill = rule_of_mixtures(values, fractions, mode="hill")
    assert reuss < hill < voigt


def test_mechanical_baselines() -> None:
    assert hall_petch_strength(100e6, 0.1e6, 1e-6) > 100e6
    assert gibson_ashby_modulus(100e9, 0.2) == pytest.approx(4e9)
    strain = thermal_strain(1e-5, 100)
    assert strain[0][0] == pytest.approx(1e-3)
    assert von_mises_stress((100e6, 0, 0, 0, 0, 0)) == pytest.approx(100e6)
    assert fracture_safety_factor(50e6, 10e6, 1e-3) > 1


def test_energy_functional_separates_exploratory_term() -> None:
    functional = EnergyFunctional(
        [
            quadratic_elastic_term(100e9),
            surface_energy_term(2.0),
            information_penalty_term(1e-3),
        ]
    )
    result = functional.evaluate(
        {
            "strain": 1e-3,
            "volume_m3": 1e-6,
            "surface_area_m2": 1e-3,
            "model_complexity": 10,
        }
    )
    assert result.total > 0
    assert result.exploratory_terms == ("information_penalty",)


def test_linear_calibration() -> None:
    calibration = fit_linear_calibration(
        [CalibrationPoint(2 * x + 1, x) for x in range(5)]
    )
    assert calibration.slope == pytest.approx(2.0)
    assert calibration.intercept == pytest.approx(1.0)
    assert calibration.r_squared == pytest.approx(1.0)


def test_instrument_agreement() -> None:
    agreement = compare_instruments(
        [1.0, 2.0, 3.0],
        [1.1, 1.9, 3.05],
        combined_standard_uncertainty=[0.1, 0.1, 0.1],
    )
    assert abs(agreement.bias) < 0.1
    assert 0 <= (agreement.coverage_within_uncertainty or 0) <= 1


def test_interval_and_quantile() -> None:
    left = Interval(0, 2, 0.95)
    right = Interval(1, 3, 0.90)
    assert left.intersect(right) == Interval(1, 2, 0.90)
    assert quantile([0, 10], 0.5) == pytest.approx(5)


def test_seeded_monte_carlo_is_reproducible() -> None:
    model = lambda parameters: parameters["a"] + parameters["b"]
    samplers = {"a": normal_sampler(1.0, 0.1), "b": uniform_sampler(0.0, 1.0)}
    first = monte_carlo(model, samplers, samples=1000, seed=7)
    second = monte_carlo(model, samplers, samples=1000, seed=7)
    assert first == second
    assert 1.3 < first.mean < 1.7


def test_sensitivity_and_uncertainty_combination() -> None:
    model = lambda p: p["x"] ** 2 + 3 * p["y"]
    sensitivities = sensitivity_finite_difference(model, {"x": 2.0, "y": 1.0})
    assert sensitivities["x"] == pytest.approx(4.0, rel=1e-5)
    assert sensitivities["y"] == pytest.approx(3.0, rel=1e-5)
    combined = combine_independent_standard_uncertainties(
        sensitivities, {"x": 0.1, "y": 0.2}
    )
    assert combined == pytest.approx(math.sqrt(0.4**2 + 0.6**2))


def test_ontology_tags_and_index() -> None:
    genomes = tuple(iter_archetypes())
    tags = classify(build_archetype("porous_ceramic"))
    assert any(tag.key == "architecture:porous" for tag in tags)
    index = index_by_tag(genomes)
    assert "order:hierarchical" in index
    assert "archetype-architected-lattice" in index["order:hierarchical"]


def test_oak_reports_all_gates() -> None:
    report = run_oak_gate(build_archetype("metallic_crystal"))
    assert len(report.gates) == 8
    assert report.status in {GateStatus.PASS, GateStatus.WARN}
    assert 0 <= report.score <= 1


def test_oak_blocks_missing_properties() -> None:
    genome = build_archetype("metallic_crystal")
    incomplete = replace(genome, properties=(), applications=(), next_experiments=())
    report = run_oak_gate(incomplete)
    assert report.status is GateStatus.FAIL
    assert report.blockers


def test_inverse_design_ranking() -> None:
    compiler = SolidCompiler(
        (
            PropertyObjective(
                "young_modulus",
                target=100e9,
                unit="Pa",
                tolerance=50e9,
                mode="maximize",
            ),
        ),
        (maximum_porosity(0.5),),
    )
    ranking = compiler.rank(iter_archetypes())
    assert len(ranking) == 12
    assert ranking[0].total_score >= ranking[-1].total_score
    assert all(0 <= candidate.total_score <= 1 for candidate in ranking)


def test_inverse_design_hard_and_soft_constraints() -> None:
    genome = build_archetype("metallic_crystal")
    compiler = SolidCompiler(
        (PropertyObjective("density", 2700, "kg/m^3", 100),),
        (
            allowed_families("ceramic"),
            require_process_step("impossible-step", hard=False),
        ),
    )
    candidate = compiler.evaluate(genome)
    assert "allowed_families" in candidate.hard_violations
    assert candidate.total_score == 0


def test_pipeline_materializes_complete_bundle(tmp_path: Path) -> None:
    pipeline = SolidPipeline()
    report = pipeline.analyze(build_archetype("semiconductor_crystal"))
    output = pipeline.materialize(report, tmp_path / "bundle")
    expected = {
        "solid-genome.json",
        "solid-hypergraph.json",
        "solid-hypergraph.graphml",
        "cvcd-signature.json",
        "oak-report.json",
        "report.json",
        "report.md",
    }
    assert expected == {path.name for path in output.iterdir()}
    payload = json.loads((output / "report.json").read_text())
    assert payload["manifest"]["genome_id"] == "archetype-semiconductor-doped-silicon"


def test_unbounded_source_is_lazy_and_unique() -> None:
    source = ArchetypeMutationSource()
    genomes = [next(source) for _ in range(30)]
    assert source.position == 30
    assert len({genome.identifier for genome in genomes}) == 30
    assert genomes[0].geometry["generator_epoch"] == 0
    assert genomes[12].geometry["generator_epoch"] == 1


def test_adaptive_frontier_streams_and_checkpoints(tmp_path: Path) -> None:
    output = tmp_path / "frontier"
    policy = FrontierPolicy(
        initial_batch=4,
        growth_factor=2.0,
        quality_floor=0.0,
        latency_target_s=100,
    )
    controller = AdaptiveSolidFrontier(output, policy=policy)
    source = ArchetypeMutationSource()
    sink = JSONLGenomeSink(output / "accepted-genomes.jsonl")
    report = controller.run(source, sink=sink, work_items=25)
    assert report.status == "completed"
    assert report.processed == 25
    assert report.accepted == 25
    assert report.final_batch_size > policy.initial_batch
    assert (output / "checkpoint.json").exists()
    assert (output / "frontier-report.json").exists()
    assert len((output / "accepted-genomes.jsonl").read_text().splitlines()) == 25


def test_adaptive_frontier_requires_a_runtime_bound(tmp_path: Path) -> None:
    controller = AdaptiveSolidFrontier(tmp_path)
    with pytest.raises(ValueError, match="finite work_items"):
        controller.run(
            ArchetypeMutationSource(),
            sink=JSONLGenomeSink(tmp_path / "values.jsonl"),
            work_items=None,
        )
