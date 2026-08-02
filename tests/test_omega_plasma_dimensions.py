from math import isfinite
from omega_plasma_t.constants import ELECTRON_MASS,PROTON_MASS
from omega_plasma_t.state import SpeciesState,GeometryState,PlasmaState
from omega_plasma_t.dimensions import compute_scales,debye_length,plasma_frequency

def fixture():
    return PlasmaState((
      SpeciesState("electron",-1,ELECTRON_MASS,1e18,3.0,1e7),
      SpeciesState("argon+",1,40*PROTON_MASS,1e18,0.1,2e5),
      SpeciesState("argon",0,40*PROTON_MASS,1e20,0.03,1e6,neutral=True),
    ),GeometryState(0.1,1,"conducting",True),magnetic_field_t=0.05,ionization_fraction=0.01)

def test_scales_positive_and_consistent():
    s=compute_scales(fixture())
    assert 0<s.debye_length_m<1e-2
    assert s.debye_number>1
    assert s.electron_plasma_frequency_hz>0
    assert len(s.species)==3
    assert all(x.thermal_speed_m_s>=0 for x in s.species)

def test_density_reduces_debye_length():
    a=SpeciesState("e",-1,ELECTRON_MASS,1e16,1)
    b=SpeciesState("e",-1,ELECTRON_MASS,1e18,1)
    assert debye_length(b)<debye_length(a)
    assert plasma_frequency(b)>plasma_frequency(a)
