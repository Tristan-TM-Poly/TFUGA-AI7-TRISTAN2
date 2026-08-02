from omega_plasma_t.dispersion import *
from omega_plasma_t.constants import PROTON_MASS
def test_branches():
    assert electron_plasma_angular_frequency(1e18)>electron_plasma_angular_frequency(1e16)
    assert langmuir_bohm_gross(10,1e18,2).omega_rad_s.real>0 and ion_acoustic(10,2,PROTON_MASS).omega_rad_s.real>0 and alfven(1,0.1,1e-9).omega_rad_s.real>0
