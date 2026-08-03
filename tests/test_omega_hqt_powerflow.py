from omega_hqt_t.outage import simulate_outage
from omega_hqt_t.scenarios import nominal, compound_ice_storm
from omega_hqt_t.synthetic_quebec import build_regions,build_corridors

def test_nominal_flow_is_finite_and_balanced():
    sim=simulate_outage(build_regions(),build_corridors(),nominal()); assert sim.flow.finite; assert sim.flow.balance_residual_mw<1e-7

def test_compound_storm_is_not_better_than_nominal_fixture():
    r=build_regions(); c=build_corridors(); assert simulate_outage(r,c,compound_ice_storm()).flow.unserved_energy_mwh>=simulate_outage(r,c,nominal()).flow.unserved_energy_mwh
