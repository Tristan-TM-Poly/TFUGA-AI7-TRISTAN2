from omega_plasma_t.constants import ELECTRON_MASS,PROTON_MASS
from omega_plasma_t.state import *
from omega_plasma_t.regime_classifier import classify_regime
def test_classifier_multilabel_and_explainable():
    s=PlasmaState((SpeciesState("electron",-1,ELECTRON_MASS,1e17,5,1e6),SpeciesState("ion",1,PROTON_MASS,1e17,0.2,1e5)),GeometryState(1.0),magnetic_field_t=0.1,ionization_fraction=1.0)
    a=classify_regime(s); assert "collective_plasma" in a.labels and any(x.label.startswith("magnetized_electron") for x in a.evidence) and not a.contradictions
