from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from hgfm import HGFM


def test_add_node_and_edge_and_incidence():
    graph = HGFM()
    idea = graph.add_node(
        type="idea",
        content="HGFM as transformative memory",
        layer="meta_theory",
        scale="meta",
        oak_status="FERTILE",
    )
    invariant = graph.add_node(
        type="invariant",
        content="Trace -> LOG -> CVCD -> OAK -> EXP",
        layer="meta_theory",
        scale="meta",
        oak_status="TESTABLE",
    )
    edge = graph.add_edge(
        type="log_cvcd_oak",
        inputs=[idea],
        outputs=[invariant],
        transform="LOG_CVCD_OAK",
        oak_status="TESTABLE",
    )

    incidence = graph.incidence()
    assert incidence[idea][edge] == -1
    assert incidence[invariant][edge] == 1


def test_omega_gate_certifies_proven_nodes():
    graph = HGFM()
    node = graph.add_node(
        type="definition",
        content="A canon object requires evidence and attack.",
        layer="epistemic",
        scale="meta",
        oak_status="PROVEN",
        scores={"logic": 0.9, "validation": 0.9},
    )

    assert graph.oak_gate(node) == "CERTIFIED"


def test_negative_memory_marks_node_neg():
    graph = HGFM()
    node = graph.add_node(
        type="claim",
        content="Fertile implies proven.",
        layer="epistemic",
        scale="meta",
        oak_status="TRACE",
    )

    graph.register_failure(
        node,
        reason="confuses fertility with proof",
        guardrail="enforce FERTILE != PROVEN",
    )

    assert graph.nodes[node].oak_status == "M_MINUS"
    assert graph.nodes[node].omegagate == "NEG"
    assert graph.m_minus
    assert "confuses fertility" in graph.m_minus[0]


def test_cvcd_candidate_heuristic():
    graph = HGFM()
    good = graph.add_node(
        type="invariant",
        content="Multi-scale stability under projection",
        layer="mathematical",
        scale="meta",
        oak_status="FERTILE",
        scores={
            "fertility": 0.9,
            "compression": 0.8,
            "stability": 0.7,
            "residue": 0.1,
            "risk": 0.1,
        },
    )
    weak = graph.add_node(
        type="idea",
        content="Unscored weak idea",
        layer="meta_theory",
        scale="micro",
        oak_status="TRACE",
        scores={"fertility": 0.1},
    )

    candidates = {node.id for node in graph.cvcd_candidates()}
    assert good in candidates
    assert weak not in candidates
