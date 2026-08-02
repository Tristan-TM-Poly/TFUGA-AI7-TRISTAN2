from dataclasses import replace

from omega_pct_t.r03max.model_generator import dark_vector_candidate, scalar_portal_candidate
from omega_pct_t.r03max.oakbench import OAKBench, OAKPolicy


def test_oak_report_has_twelve_gates():
    report = OAKBench().evaluate(scalar_portal_candidate())
    assert len(report.gate_results) == 12
    assert report.metadata["fingerprint"]


def test_missing_falsifier_blocks_falsification_gate():
    theory = replace(dark_vector_candidate(), falsifiers=())
    report = OAKBench(OAKPolicy(require_falsifier=True)).evaluate(theory)
    assert report.gate_results["falsification"] is False
    assert any(item.code == "FALSIFIER_MISSING" for item in report.findings)


def test_uncancelled_anomaly_blocks_quantum_gate():
    from fractions import Fraction
    from omega_pct_t.r03max.types import Chirality, EpistemicStatus, FieldKind, FieldSpec, GaugeCharge, OntologyLevel, TheorySpec

    field = FieldSpec(
        id="chi",
        name="chi",
        kind=FieldKind.FERMION,
        lorentz_representation="Weyl",
        mass_dimension=Fraction(3, 2),
        ontology_level=OntologyLevel.HYPOTHETICAL,
        status=EpistemicStatus.HYPOTHETICAL,
        chirality=Chirality.LEFT,
        gauge_charges=(GaugeCharge.from_number("U1X", "fundamental", 1),),
    )
    theory = TheorySpec("bad", "bad", EpistemicStatus.HYPOTHETICAL, None, ("U1X",), (field,), (), (), ())
    report = OAKBench().evaluate(theory)
    assert report.gate_results["quantum_consistency"] is False
