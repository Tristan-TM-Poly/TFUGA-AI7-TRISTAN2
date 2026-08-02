from itertools import islice

from omega_org_fam_t.classifier import classify_features
from omega_org_fam_t.family_space import base_coordinates, evidence_templates, family_cells, iter_requested_cells
from omega_org_fam_t.hypergraph import build_hypergraph
from omega_org_fam_t.oak import oak_gate_for_identification


def test_default_lattice_has_262144_unique_cells():
    cells = list(family_cells())
    assert len(cells) == 262_144
    assert len({cell.id for cell in cells}) == 262_144
    assert cells[0].id == "ORG-FAM-00000000"
    assert cells[-1].id == "ORG-FAM-00262143"


def test_each_cell_has_three_linked_evidence_templates():
    cells = list(islice(iter_requested_cells(128), 128))
    evidence = list(evidence_templates(cells))
    assert len(evidence) == 384
    assert {item.family_id for item in evidence} == {cell.id for cell in cells}


def test_classifier_prefers_matching_functional_family():
    cells = list(islice(iter_requested_cells(262_144), 262_144))
    result = classify_features(cells, {"alcohol_phenol", "O-H environment"}, top_k=20)
    ids = {family_id for family_id, _ in result.ranked_family_ids}
    indexed = {cell.id: cell for cell in cells}
    assert all(indexed[item].coordinate.functional_family == "alcohol_phenol" for item in ids)


def test_hypergraph_rejects_orphan_evidence():
    cells = list(islice(iter_requested_cells(2), 2))
    evidence = list(evidence_templates(cells))
    graph = build_hypergraph(cells, evidence)
    assert len(graph["hyperedges"]) == 2 * 6 + 6
    assert graph["oak_boundary"]


def test_oak_gate_requires_independent_convergence():
    assert oak_gate_for_identification(independent_modalities=0, contradictions=0, reference_match=False) == "candidate_cell_unvalidated"
    assert oak_gate_for_identification(independent_modalities=2, contradictions=0, reference_match=False) == "multimodal_evidence"
    assert oak_gate_for_identification(independent_modalities=2, contradictions=0, reference_match=True) == "reference_confirmed"


def test_arbitrary_finite_experiment_exceeds_default_lattice():
    cells = list(islice(iter_requested_cells(270_000), 270_000))
    assert len(cells) == 270_000
    assert cells[-1].id == "ORG-FAM-00269999"
    assert "epoch_1" in cells[-1].provenance
