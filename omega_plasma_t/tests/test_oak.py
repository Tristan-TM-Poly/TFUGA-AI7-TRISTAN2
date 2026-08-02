from omega_plasma_t.constants import *
from omega_plasma_t.state import *
from omega_plasma_t.oak import audit_state
def test_oak():
    s=PlasmaState((SpeciesState("e",-1,ELECTRON_MASS,1e18,2,1e6),SpeciesState("p",1,PROTON_MASS,1e18,0.2,1e5)),GeometryState(0.1,surface_present=True),magnetic_field_t=0.01)
    r=audit_state(s); codes={x.code for x in r.findings}; assert {"SHEATH_REQUIRED","TARGET_UNSPECIFIED"}<=codes and r.status=="review"
def test_invalid_blocked(): assert audit_state(PlasmaState((SpeciesState("e",-1,-1,1,1),),GeometryState(1))).status=="blocked"
