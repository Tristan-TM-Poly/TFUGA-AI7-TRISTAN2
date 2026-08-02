from omega_plasma_t.constants import *
from omega_plasma_t.state import *
from omega_plasma_t.model_compiler import compile_models

def test_partial_surface_plasma_recommends_multiphysics():
    s=PlasmaState((SpeciesState("electron",-1,ELECTRON_MASS,1e16,4,1e7),SpeciesState("Ar+",1,40*ATOMIC_MASS_UNIT,1e16,0.1,1e6),SpeciesState("Ar",0,40*ATOMIC_MASS_UNIT,1e20,0.03,1e8,neutral=True)),GeometryState(0.03,2,"conducting",True),magnetic_field_t=0.02,ionization_fraction=1e-4,requested_observables=("ion_flux",))
    d=compile_models(s)
    names={x.name for x in d.recommended}
    assert "multi_fluid" in names
    assert "surface_reaction_model" in names
    assert "sheath_model" in names
